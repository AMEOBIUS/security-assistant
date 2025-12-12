"""
Command Executor Utility

Provides unified subprocess execution with:
- Timeout management
- Error handling
- Logging
- Output capturing
"""

import logging
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class CommandExecutionError(Exception):
    """Command execution failed."""
    pass


@dataclass
class CommandResult:
    """Result of command execution."""
    returncode: int
    stdout: str
    stderr: str
    command: List[str]


class CommandExecutor:
    """Unified command executor."""
    
    @staticmethod
    def run(
        command: List[str],
        timeout: int = 300,
        check: bool = True,
        cwd: Optional[str] = None,
        valid_return_codes: Optional[List[int]] = None
    ) -> CommandResult:
        """
        Execute a shell command.
        
        Args:
            command: Command and arguments
            timeout: Timeout in seconds
            check: Raise exception on failure (default: True)
            cwd: Working directory
            valid_return_codes: List of allowed return codes (default: [0])
            
        Returns:
            CommandResult object
            
        Raises:
            CommandExecutionError: If command fails or times out
        """
        logger.debug("Running command: %s", " ".join(command))
        
        if valid_return_codes is None:
            valid_return_codes = [0]
            
        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd
            )
            
            result = CommandResult(
                returncode=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
                command=command
            )
            
            if check and process.returncode not in valid_return_codes:
                error_msg = process.stderr.strip() or process.stdout.strip() or "Unknown error"
                logger.error("Command failed with code %d: %s", process.returncode, error_msg)
                raise CommandExecutionError(
                    f"Command failed with code {process.returncode}: {error_msg}"
                )
                
            return result
            
        except subprocess.TimeoutExpired as e:
            logger.error("Command timed out after %d seconds: %s", timeout, " ".join(command))
            raise CommandExecutionError(f"Command timed out after {timeout}s") from e
            
        except Exception as e:
            logger.error("Failed to execute command: %s", e)
            raise CommandExecutionError(f"Failed to execute command: {e}") from e
