"""
Shell Execution Tool Handler

Execute shell commands with security guards and sandboxing.
"""

import asyncio
import re
import shlex
from pathlib import Path
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

# Dangerous command patterns
DANGEROUS_PATTERNS = [
    r'\brm\s+-rf\b',
    r'\brm\s+-r\b.*--no-preserve-root',
    r'\bmkfs\b',
    r'\bdd\b.*(if=|of=)',
    r'\bchmod\s+777\b',
    r'\bchmod\s+-R\s+777\b',
    r'\b shred\b',
    r'\bnuke\b',
    r'\bfork\s*bomb\b',
    r':(){ :|:& };:',
    r'\b>\s*/\s*dev\s*/\s*null\b',
    r'\b>\s*/\s*dev\s*/\s*zero\b',
    r'\bcat\s+/proc/\s*self\s*/\s*cmdline\b',
]

# Allowed commands (whitelist approach)
ALLOWED_COMMANDS = {
    'ls', 'cat', 'echo', 'pwd', 'cd', 'mkdir', 'touch', 'rm', 'cp', 'mv',
    'grep', 'find', 'head', 'tail', 'wc', 'sort', 'uniq', 'cut', 'sed',
    'awk', 'diff', 'patch', 'tar', 'gzip', 'gunzip', 'zip', 'unzip',
    'git', 'npm', 'pip', 'python', 'python3', 'node', 'curl', 'wget',
    'ping', 'traceroute', 'netstat', 'ss', 'ps', 'top', 'htop',
    'chmod', 'chown', 'ln', 'readlink', 'realpath', 'basename', 'dirname',
    'date', 'cal', 'whoami', 'id', 'uname', 'hostname', 'uptime',
}

# Work directory for sandboxing
WORKSPACE_ROOT: Optional[Path] = None


class BaseExecHandler(ABC):
    """Base class for execution handlers."""
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute the command."""
        pass
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve and validate path within workspace."""
        if WORKSPACE_ROOT is None:
            global WORKSPACE_ROOT
            WORKSPACE_ROOT = Path.cwd()
        
        resolved = Path(path).resolve()
        
        try:
            resolved.relative_to(WORKSPACE_ROOT)
        except ValueError:
            raise SecurityError(f"Access denied: {path} is outside workspace")
        
        return resolved
    
    def _validate_command(self, command: str) -> None:
        """Validate command for security."""
        # Check for dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                raise SecurityError(f"Dangerous command pattern detected: {pattern}")
        
        # Check command whitelist
        parts = shlex.split(command)
        if parts:
            cmd = parts[0]
            if cmd not in ALLOWED_COMMANDS:
                # Allow if it's a relative path or absolute path
                if not ('/' in cmd or '\\' in cmd):
                    raise SecurityError(f"Command not allowed: {cmd}")


class ExecTool(BaseExecHandler):
    """
    Execute shell commands with security guards.
    
    Parameters:
        cmd: Command to execute (required)
        timeout: Timeout in seconds (default: 30)
        cwd: Working directory (default: workspace root)
        env: Environment variables (optional)
    
    Returns:
        Command output (stdout + stderr)
    
    Security Features:
    - Dangerous command pattern detection
    - Command whitelist
    - Workspace restriction
    - Timeout protection
    """
    
    def __init__(self, workspace_root: Optional[str] = None):
        global WORKSPACE_ROOT
        if workspace_root:
            WORKSPACE_ROOT = Path(workspace_root)
        else:
            WORKSPACE_ROOT = Path.cwd()
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute shell command."""
        try:
            cmd = arguments.get("cmd")
            if not cmd:
                raise ValueError("Missing required parameter: cmd")
            
            # Validate command
            self._validate_command(cmd)
            
            # Get timeout
            timeout = float(arguments.get("timeout", 30))
            
            # Get working directory
            cwd = arguments.get("cwd")
            if cwd:
                cwd = self._resolve_path(cwd)
            else:
                cwd = WORKSPACE_ROOT
            
            # Get environment variables
            env = arguments.get("env")
            if env:
                import os
                full_env = os.environ.copy()
                full_env.update(env)
            else:
                full_env = None
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd),
                env=full_env,
                limit=1024 * 1024  # 1MB output limit
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                raise TimeoutError(f"Command timed out after {timeout} seconds")
            
            # Combine outputs
            output_parts = []
            if stdout:
                output_parts.append(stdout.decode('utf-8', errors='replace'))
            if stderr:
                output_parts.append(f"STDERR:\n{stderr.decode('utf-8', errors='replace')}")
            
            output = ''.join(output_parts)
            
            # Check return code
            if process.returncode != 0:
                output += f"\n[Exit code: {process.returncode}]"
            
            return output
            
        except SecurityError:
            raise
        except TimeoutError:
            raise
        except Exception as e:
            raise RuntimeError(f"Command execution failed: {e}")
    
    def get_parameters(self) -> Dict[str, Any]:
        """Return tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "cmd": {
                    "type": "string",
                    "description": "Command to execute"
                },
                "timeout": {
                    "type": "number",
                    "description": "Timeout in seconds",
                    "default": 30
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory"
                },
                "env": {
                    "type": "object",
                    "description": "Environment variables"
                }
            },
            "required": ["cmd"]
        }


class SecurityError(Exception):
    """Security violation exception."""
    pass


class CommandTimeoutError(Exception):
    """Command execution timeout."""
    pass
