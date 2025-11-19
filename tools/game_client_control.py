import subprocess
import time
import pyautogui
import base64
from io import BytesIO
import psutil
from config import GAME_CONFIG

class GameClientControl:
    """
    Controls the game client using process management and GUI automation (pyautogui).
    NOTE: This requires a running X server environment (GUI) to work properly.
    """
    @staticmethod
    def launch_game():
        """Launches the game executable."""
        print(f"Launching game from: {GAME_CONFIG['GAME_PATH']}")
        try:
            subprocess.Popen([GAME_CONFIG['GAME_PATH']])
            time.sleep(5) # Give time for the game to start
            return True
        except FileNotFoundError:
            print(f"Error: Game executable not found at {GAME_CONFIG['GAME_PATH']}")
            return False

    @staticmethod
    def is_game_running(process_name: str = "RebirthRC.exe") -> bool:
        """Checks if the game process is currently running."""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == process_name:
                return True
        return False

    @staticmethod
    def close_game(process_name: str = "RebirthRC.exe"):
        """Terminates the game process."""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == process_name:
                proc.terminate()
                print(f"Game process {process_name} terminated.")
                return

    @staticmethod
    def perform_action(action_type: str, payload: dict):
        """
        Performs a simulated user action (e.g., click, type).
        :param action_type: 'click', 'type', 'screenshot'.
        :param payload: Dictionary containing action parameters.
        """
        if not GameClientControl.is_game_running():
            print("Game is not running. Cannot perform action.")
            return False

        if action_type == 'click':
            x, y = payload.get('x'), payload.get('y')
            if x is not None and y is not None:
                pyautogui.click(x, y)
                print(f"Clicked at ({x}, {y})")
                return True
        
        elif action_type == 'type':
            text = payload.get('text')
            if text is not None:
                pyautogui.typewrite(text)
                print(f"Typed: {text}")
                return True

        elif action_type == 'screenshot':
            path = payload.get('path', 'game_screenshot.png')
            pyautogui.screenshot(path)
            print(f"Screenshot saved to {path}")
            return True

        elif action_type == 'get_screenshot_base64':
            # Captures screenshot and returns it as a base64 string for AI Vision
            screenshot = pyautogui.screenshot()
            buffered = BytesIO()
            screenshot.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            print("Captured screenshot as base64 string.")
            return img_str
            
        return False

# Example: If the game is already running (as per user's current scenario)
# You would use perform_action to simulate in-game actions for the Observer/Planner
