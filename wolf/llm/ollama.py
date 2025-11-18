"""
Wolf CLI Ollama Adapter

Adapter for Ollama API with tool-calling and vision support.
"""

import base64
import json
import requests
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.logging_utils import log_debug, log_error, log_warn


class OllamaAdapter:
    """Ollama API adapter with tool and vision support"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        self.base_url = base_url.rstrip("/")
        self.model = model
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image file to base64"""
        try:
            path = Path(image_path)
            # Resolve to absolute path
            path = path.resolve()
            
            if not path.exists():
                raise FileNotFoundError(f"Image not found: {image_path} (resolved: {path})")
            
            if not path.is_file():
                raise ValueError(f"Path is not a file: {image_path}")
            
            # Check file size (warn if very large)
            file_size = path.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB
                log_warn(f"Image file is large ({file_size / 1024 / 1024:.1f}MB): {image_path}")
            
            with open(path, 'rb') as f:
                image_data = f.read()
                encoded = base64.b64encode(image_data).decode('utf-8')
                log_debug(f"Encoded image: {image_path} ({len(image_data)} bytes -> {len(encoded)} base64 chars)")
                return encoded
        except FileNotFoundError as e:
            log_error(f"Image file not found: {str(e)}")
            raise
        except Exception as e:
            log_error(f"Error encoding image '{image_path}': {str(e)}", exc_info=True)
            raise
    
    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        images: Optional[List[str]] = None,
        images_base64: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send chat request to Ollama
        
        Args:
            messages: List of message dicts
            tools: Optional list of tool schemas
            images: Optional list of image paths
            
        Returns:
            Response dictionary with 'choices' and 'message' content
        """
        url = f"{self.base_url}/api/chat"
        
        # Encode images if provided
        encoded_images = []
        if images:
            log_debug(f"Encoding {len(images)} image(s) for vision model")
            for img_path in images:
                try:
                    encoded = self._encode_image(img_path)
                    if encoded:
                        encoded_images.append(encoded)
                        log_debug(f"Successfully encoded image: {img_path}")
                    else:
                        log_error(f"Failed to encode image (empty result): {img_path}")
                except Exception as e:
                    log_error(f"Failed to encode image '{img_path}': {e}")
                    # Continue with other images rather than failing completely
                    continue
        
        if images_base64:
            encoded_images.extend(images_base64)
            
        # Only error if images were provided but encoding failed
        if (images or images_base64) and not encoded_images:
            log_error("Images were provided but encoding failed!")
            return {
                "choices": [],
                "error": "Failed to encode any images for vision processing",
            }
        
        # Add images to last user message
        if encoded_images and messages:
            image_added = False
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    # Ensure content field exists (required by Ollama API)
                    if "content" not in msg:
                        msg["content"] = ""
                    msg["images"] = encoded_images
                    image_added = True
                    log_debug(f"Added {len(encoded_images)} image(s) to user message")
                    break
            
            if not image_added:
                log_warn("Could not find user message to attach images to!")
                # Create a new user message with images if no user message found
                messages.append({
                    "role": "user",
                    "content": "",
                    "images": encoded_images
                })
                log_debug("Created new user message with images")
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        
        # Log request details (without full base64 image data)
        image_count = 0
        for msg in messages:
            if "images" in msg:
                image_count += len(msg.get("images", []))
        
        log_debug(f"Ollama request: model={self.model}, messages={len(messages)}, tools={len(tools) if tools else 0}, images={image_count}")
        if image_count > 0:
            log_debug(f"Sending {image_count} image(s) to vision model {self.model}")
        
        # Some vision models don't support tools - skip tools proactively for known vision-only models
        # This avoids the 400 error and retry cycle
        vision_only_models = ["qwen3-vl:8b", "llava-llama3:8b", "llava", "qwen-vl"]
        is_vision_only = any(vm in self.model.lower() for vm in vision_only_models)
        
        # Add tools if provided, but skip for vision-only models
        if tools and not (image_count > 0 and is_vision_only):
            payload["tools"] = tools
        elif tools and image_count > 0 and is_vision_only:
            log_debug(f"Skipping tools for vision-only model: {self.model}")
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            
            # Check for errors and log detailed response
            if not response.ok:
                error_detail = "Unknown error"
                try:
                    error_data = response.json()
                    # Ollama error format can be {"error": "message"} or {"error": {"message": "..."}}
                    if isinstance(error_data.get("error"), dict):
                        error_detail = error_data.get("error", {}).get("message", str(error_data))
                    elif "error" in error_data:
                        error_detail = str(error_data["error"])
                    else:
                        error_detail = str(error_data)
                except:
                    error_detail = response.text or str(response.status_code)
                
                # If we got a 400 error with both images and tools, try without tools
                # Some vision models don't support tool calling
                if response.status_code == 400 and image_count > 0 and tools:
                    # Silently retry without tools - this is expected behavior for some vision models
                    log_debug(f"Vision model doesn't support tools, retrying without tools: {error_detail}")
                    # Retry without tools
                    payload_no_tools = payload.copy()
                    payload_no_tools.pop("tools", None)
                    
                    try:
                        retry_response = requests.post(url, json=payload_no_tools, timeout=120)
                        if retry_response.ok:
                            log_debug("Retry without tools succeeded")
                            data = retry_response.json()
                            message = data.get("message", {})
                            # Ensure message has content field
                            if "content" not in message:
                                message["content"] = ""
                            log_debug(f"Retry response message content length: {len(message.get('content', ''))}")
                            return {
                                "choices": [
                                    {
                                        "message": message,
                                        "finish_reason": "stop",
                                    }
                                ],
                            }
                        else:
                            # Still failed, return original error
                            retry_error = "Unknown error"
                            try:
                                retry_error_data = retry_response.json()
                                if isinstance(retry_error_data.get("error"), dict):
                                    retry_error = retry_error_data.get("error", {}).get("message", str(retry_error_data))
                                elif "error" in retry_error_data:
                                    retry_error = str(retry_error_data["error"])
                            except:
                                retry_error = retry_response.text or str(retry_response.status_code)
                            log_error(f"Retry without tools also failed: {retry_response.status_code} - {retry_error}")
                    except Exception as retry_e:
                        log_error(f"Error during retry without tools: {retry_e}")
                
                # Only show error if we didn't handle it with fallback
                log_error(f"Ollama API error: {error_detail}")
                return {
                    "choices": [],
                    "error": f"{response.status_code} {response.reason}: {error_detail}",
                }
            
            response.raise_for_status()
            
            data = response.json()
            log_debug(f"Ollama response received")
            
            message = data.get("message", {})
            
            # Ensure message has content field (some models might not include it)
            if "content" not in message:
                message["content"] = ""
            
            # Log content length for debugging (only in debug mode)
            content_length = len(message.get("content", ""))
            log_debug(f"Response message content length: {content_length}")
            
            # Format response to match OpenAI-style structure
            return {
                "choices": [
                    {
                        "message": message,
                        "finish_reason": "stop" if not message.get("tool_calls") else "tool_calls",
                    }
                ],
            }
        
        except requests.exceptions.RequestException as e:
            log_error(f"Ollama API error: {str(e)}")
            return {
                "choices": [],
                "error": str(e),
            }
        except Exception as e:
            log_error(f"Unexpected error: {str(e)}", exc_info=True)
            return {
                "choices": [],
                "error": str(e),
            }


# Module-level function for easy access
def chat(model: str, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, base_url: str = "http://localhost:11434", images: Optional[List[str]] = None, images_base64: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Convenience function for chat requests
    
    Args:
        model: Model name
        messages: List of message dicts
        tools: Optional list of tool schemas
        base_url: Ollama API base URL
        images: Optional list of image paths
        images_base64: Optional list of base64-encoded images
        
    Returns:
        Response dictionary
    """
    adapter = OllamaAdapter(base_url=base_url, model=model)
    return adapter.chat(messages=messages, tools=tools, images=images, images_base64=images_base64)
