import time
import pyautogui
import pyperclip
import keyboard
import win32gui
import win32con
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

### ---------- CONFIG ----------
CURSOR_WINDOW_TITLE = "Cursor"
AI_SHORTCUT = "ctrl+k"
WAIT_AFTER_SHORTCUT = 0.4
WAIT_FOR_RESPONSE = 2.5
### ----------------------------


def focus_cursor_window():
    def enum_handler(hwnd, windows):
        if CURSOR_WINDOW_TITLE.lower() in win32gui.GetWindowText(hwnd).lower():
            windows.append(hwnd)
    found = []
    win32gui.EnumWindows(enum_handler, found)
    if not found:
        return False
    hwnd = found[0]

    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    return True


def send_to_cursor(prompt: str):
    if not focus_cursor_window():
        return {"error": "Cursor window not found"}

    time.sleep(0.25)

    # Open AI command panel (Ctrl + K)
    keyboard.press_and_release(AI_SHORTCUT)
    time.sleep(WAIT_AFTER_SHORTCUT)

    # Paste prompt
    pyperclip.copy(prompt)
    keyboard.press_and_release("ctrl+v")
    time.sleep(0.2)

    # Submit prompt
    keyboard.press_and_release("enter")
    time.sleep(WAIT_FOR_RESPONSE)

    # Copy AI response
    keyboard.press_and_release("ctrl+a")
    time.sleep(0.1)
    keyboard.press_and_release("ctrl+c")
    time.sleep(0.2)

    output = pyperclip.paste()
    return {"response": output}


class Prompt(BaseModel):
    prompt: str


@app.post("/cursor/prompt")
def cursor_prompt(p: Prompt):
    return send_to_cursor(p.prompt)
