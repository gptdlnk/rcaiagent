import subprocess
import time
import os
import platform
import pyautogui
import psutil
from config import GAME_CONFIG, SCREENSHOT_DIR

class GameClientControl:
    """
    Controls the game client using process management and GUI automation (pyautogui).
    Supports both Windows and Linux environments.
    """
    
    @staticmethod
    def _expand_path(path: str) -> str:
        """Expand environment variables and user home directory in path."""
        if not path:
            return path
        # Expand environment variables (Windows: %VAR%, Unix: $VAR)
        path = os.path.expandvars(path)
        # Expand user home directory
        path = os.path.expanduser(path)
        return path
    
    @staticmethod
    def launch_game() -> bool:
        """Launches the game executable."""
        game_path = GameClientControl._expand_path(GAME_CONFIG.get('GAME_PATH', ''))
        
        if not game_path or game_path == "/path/to/RebirthRC.exe":
            print("Error: GAME_PATH not configured. Please set GAME_PATH in config.py or .env file.")
            return False
        
        if not os.path.exists(game_path):
            print(f"Error: Game executable not found at {game_path}")
            return False
        
        print(f"Launching game from: {game_path}")
        try:
            # Use shell=True on Windows for .exe files
            if platform.system() == 'Windows':
                subprocess.Popen(game_path, shell=True)
            else:
                subprocess.Popen([game_path])
            
            # Wait for game to start and check if it's running
            max_wait = 10
            for i in range(max_wait):
                time.sleep(1)
                if GameClientControl.is_game_running():
                    print(f"Game started successfully after {i+1} seconds.")
                    return True
            
            print("Warning: Game launch initiated but process not detected after 10 seconds.")
            return False
            
        except Exception as e:
            print(f"Error launching game: {e}")
            return False

    @staticmethod
    def is_game_running(process_name: str = None) -> bool:
        """Checks if the game process is currently running."""
        if process_name is None:
            process_name = GAME_CONFIG.get('GAME_PROCESS_NAME', 'RebirthRC.exe')
        
        try:
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception as e:
            print(f"Error checking game process: {e}")
            return False

    @staticmethod
    def close_game(process_name: str = None) -> bool:
        """Terminates the game process."""
        if process_name is None:
            process_name = GAME_CONFIG.get('GAME_PROCESS_NAME', 'RebirthRC.exe')
        
        try:
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
                        proc.terminate()
                        print(f"Game process {process_name} (PID: {proc.info['pid']}) terminated.")
                        # Wait a bit for graceful termination
                        time.sleep(2)
                        # Force kill if still running
                        if proc.is_running():
                            proc.kill()
                            print(f"Game process {process_name} force killed.")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    continue
            print(f"Game process {process_name} not found.")
            return False
        except Exception as e:
            print(f"Error closing game: {e}")
            return False

    @staticmethod
    def perform_action(action_type: str, payload: dict) -> bool:
        """
        Performs a simulated user action (e.g., click, type, screenshot).
        :param action_type: 'click', 'type', 'screenshot'.
        :param payload: Dictionary containing action parameters.
        :return: True if successful, False otherwise.
        """
        if not GameClientControl.is_game_running():
            print("Game is not running. Cannot perform action.")
            return False

        try:
            if action_type == 'click':
                x, y = payload.get('x'), payload.get('y')
                if x is not None and y is not None:
                    pyautogui.click(x, y)
                    print(f"Clicked at ({x}, {y})")
                    return True
                else:
                    print(f"Error: Missing x or y coordinates in payload: {payload}")
                    return False
            
            elif action_type == 'type':
                text = payload.get('text')
                if text is not None:
                    pyautogui.typewrite(text, interval=0.1)  # Add small delay between keystrokes
                    print(f"Typed: {text}")
                    return True
                else:
                    print(f"Error: Missing 'text' in payload: {payload}")
                    return False

            elif action_type == 'screenshot':
                # Ensure screenshot directory exists
                os.makedirs(SCREENSHOT_DIR, exist_ok=True)
                
                filename = payload.get('filename', f'screenshot_{int(time.time())}.png')
                path = os.path.join(SCREENSHOT_DIR, filename)
                
                screenshot = pyautogui.screenshot()
                screenshot.save(path)
                print(f"Screenshot saved to {path}")
                return True
            
            else:
                print(f"Error: Unknown action type: {action_type}")
                return False
                
        except Exception as e:
            print(f"Error performing action {action_type}: {e}")
            return False

# Example: If the game is already running (as per user's current scenario)
# You would use perform_action to simulate in-game actions for the Observer/Planner
