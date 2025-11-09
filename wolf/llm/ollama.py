"""
Wolf CLI Ollama Adapter

Adapter for Ollama API with tool-calling and vision support.
"""

import base64
import json
import requests
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.logging_utils import log_debug, log_error


class OllamaAdapter:
    """Ollama API adapter with tool and vision support"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        self.base_url = base_url.rstrip("/")
        self.model = model
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image file to base64"""
        try:
            path = Path(image_path)
            if not path.exists():
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            with open(path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            log_error(f"Error encoding image: {str(e)}")
            return ""
    
    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        images: Optional[List[str]] = None,
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
            for img_path in images:
                encoded = self._encode_image(img_path)
                if encoded:
                    encoded_images.append(encoded)
        
        # Add images to last user message
        if encoded_images and messages:
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    msg["images"] = encoded_images
                    break
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        
        # Add tools if provided
        if tools:
            payload["tools"] = tools
        
        log_debug(f"Ollama request: model={self.model}, messages={len(messages)}, tools={len(tools) if tools else 0}")
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            data = response.json()
            log_debug(f"Ollama response received")
            
            message = data.get("message", {})
            
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
def chat(model: str, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, base_url: str = "http://localhost:11434", images: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Convenience function for chat requests
    
    Args:
        model: Model name
        messages: List of message dicts
        tools: Optional list of tool schemas
        base_url: Ollama API base URL
        images: Optional list of image paths
        
    Returns:
        Response dictionary
    """
    adapter = OllamaAdapter(base_url=base_url, model=model)
    return adapter.chat(messages=messages, tools=tools, images=images)
