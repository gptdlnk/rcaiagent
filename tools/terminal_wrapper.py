import subprocess
from typing import Tuple

class TerminalWrapper:
    """
    Wrapper for executing shell commands securely and capturing output.
    """
    @staticmethod
    def run_command(command: str, timeout: int = 60) -> Tuple[int, str, str]:
        """
        Executes a shell command.
        :param command: The command string to execute.
        :param timeout: Timeout in seconds.
        :return: Tuple of (return_code, stdout, stderr).
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False # Do not raise exception on non-zero exit code
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", f"Command timed out after {timeout} seconds."
        except Exception as e:
            return 1, "", f"An unexpected error occurred: {e}"

# Example usage (for testing)
if __name__ == "__main__":
    code, out, err = TerminalWrapper.run_command("ls -l")
    print(f"Code: {code}\nOutput: {out}\nError: {err}")
    
    code, out, err = TerminalWrapper.run_command("ping -c 4 8.8.8.8")
    print(f"Code: {code}\nOutput: {out}\nError: {err}")
