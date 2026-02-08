"""
File System Tool Handlers

Tools for reading, writing, editing, and listing files.
Includes workspace restriction for security.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

# Workspace root - should be configured at startup
WORKSPACE_ROOT: Optional[Path] = None


class BaseFileHandler(ABC):
    """Base class for file system tools."""
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute the file operation."""
        pass
    
    def _resolve_path(self, file_path: str) -> Path:
        """Resolve and validate file path within workspace."""
        global WORKSPACE_ROOT
        if WORKSPACE_ROOT is None:
            # Try to detect workspace from current directory
            WORKSPACE_ROOT = Path.cwd()
        
        resolved = Path(file_path).resolve()
        
        # Ensure path is within workspace
        try:
            resolved.relative_to(WORKSPACE_ROOT)
        except ValueError:
            raise SecurityError(f"Access denied: {file_path} is outside workspace")
        
        return resolved
    
    def _ensure_parent_exists(self, path: Path) -> None:
        """Ensure parent directory exists."""
        path.parent.mkdir(parents=True, exist_ok=True)


class ReadFileTool(BaseFileHandler):
    """
    Read file contents from the filesystem.
    
    Parameters:
        path: Path to file to read (required)
        encoding: File encoding (default: utf-8)
    
    Returns:
        File contents as string
    """
    
    def __init__(self, workspace_root: Optional[str] = None):
        global WORKSPACE_ROOT
        if workspace_root:
            WORKSPACE_ROOT = Path(workspace_root)
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Read file contents."""
        try:
            file_path = arguments.get("path")
            if not file_path:
                raise ValueError("Missing required parameter: path")
            
            path = self._resolve_path(file_path)
            
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if not path.is_file():
                raise IsADirectoryError(f"Path is a directory: {file_path}")
            
            encoding = arguments.get("encoding", "utf-8")
            
            # Read file with proper error handling
            try:
                content = path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                # Try with error replacement
                content = path.read_text(encoding="utf-8", errors="replace")
            
            return content
            
        except SecurityError:
            raise
        except Exception as e:
            raise IOError(f"Failed to read file {file_path}: {e}")
    
    def get_parameters(self) -> Dict[str, Any]:
        """Return tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to file to read"
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)",
                    "default": "utf-8"
                }
            },
            "required": ["path"]
        }


class WriteFileTool(BaseFileHandler):
    """
    Write content to a file, creating it if necessary.
    
    Parameters:
        path: Path to file to write (required)
        content: Content to write (required)
        mode: write_to_file mode - 'w' (overwrite), 'a' (append) (default: 'w')
        encoding: File encoding (default: utf-8)
    
    Returns:
        Success message
    """
    
    def __init__(self, workspace_root: Optional[str] = None):
        global WORKSPACE_ROOT
        if workspace_root:
            WORKSPACE_ROOT = Path(workspace_root)
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Write content to file."""
        try:
            file_path = arguments.get("path")
            content = arguments.get("content")
            
            if not file_path:
                raise ValueError("Missing required parameter: path")
            
            if content is None:
                raise ValueError("Missing required parameter: content")
            
            path = self._resolve_path(file_path)
            self._ensure_parent_exists(path)
            
            mode = arguments.get("mode", "w")
            encoding = arguments.get("encoding", "utf-8")
            
            if mode == "a":
                path.write_text(content, encoding=encoding)
                return f"Appended to {file_path}"
            else:
                path.write_text(content, encoding=encoding)
                return f"Written to {file_path}"
                
        except SecurityError:
            raise
        except Exception as e:
            raise IOError(f"Failed to write file {file_path}: {e}")
    
    def get_parameters(self) -> Dict[str, Any]:
        """Return tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to file to write"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to file"
                },
                "mode": {
                    "type": "string",
                    "enum": ["w", "a"],
                    "description": "Write mode: 'w' (overwrite) or 'a' (append)",
                    "default": "w"
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)",
                    "default": "utf-8"
                }
            },
            "required": ["path", "content"]
        }


class EditFileTool(BaseFileHandler):
    """
    Edit a file by replacing specific text with new content.
    
    Parameters:
        path: Path to file to edit (required)
        find: Text to find (required)
        replace: Text to replace with (required)
        count: Number of occurrences to replace (default: 1, -1 for all)
    
    Returns:
        Success message with number of replacements
    """
    
    def __init__(self, workspace_root: Optional[str] = None):
        global WORKSPACE_ROOT
        if workspace_root:
            WORKSPACE_ROOT = Path(workspace_root)
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Edit file contents."""
        try:
            file_path = arguments.get("path")
            find_text = arguments.get("find")
            replace_text = arguments.get("replace")
            
            if not file_path:
                raise ValueError("Missing required parameter: path")
            
            if find_text is None:
                raise ValueError("Missing required parameter: find")
            
            if replace_text is None:
                raise ValueError("Missing required parameter: replace")
            
            path = self._resolve_path(file_path)
            
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Read current content
            content = path.read_text(encoding="utf-8")
            
            # Perform replacement
            count = int(arguments.get("count", 1))
            if count == -1:
                new_content = content.replace(find_text, replace_text)
                replacement_count = new_content.count(content.replace(find_text, "")) - content.count(find_text)
            else:
                new_content = content.replace(find_text, replace_text, count)
                replacement_count = 1 if content != new_content else 0
            
            # Write back
            path.write_text(new_content, encoding="utf-8")
            
            return f"Replaced {replacement_count} occurrence(s) in {file_path}"
            
        except SecurityError:
            raise
        except Exception as e:
            raise IOError(f"Failed to edit file {file_path}: {e}")
    
    def get_parameters(self) -> Dict[str, Any]:
        """Return tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to file to edit"
                },
                "find": {
                    "type": "string",
                    "description": "Text to find in file"
                },
                "replace": {
                    "type": "string",
                    "description": "Text to replace with"
                },
                "count": {
                    "type": "integer",
                    "description": "Number of replacements (-1 for all)",
                    "default": 1
                }
            },
            "required": ["path", "find", "replace"]
        }


class ListDirTool(BaseFileHandler):
    """
    List directory contents.
    
    Parameters:
        path: Path to directory (default: current directory)
        include_hidden: Include hidden files (default: False)
    
    Returns:
        JSON string with directory listing
    """
    
    def __init__(self, workspace_root: Optional[str] = None):
        global WORKSPACE_ROOT
        if workspace_root:
            WORKSPACE_ROOT = Path(workspace_root)
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """List directory contents."""
        try:
            dir_path = arguments.get("path", ".")
            include_hidden = arguments.get("include_hidden", False)
            
            path = self._resolve_path(dir_path)
            
            if not path.exists():
                raise FileNotFoundError(f"Directory not found: {dir_path}")
            
            if not path.is_dir():
                raise NotADirectoryError(f"Path is not a directory: {dir_path}")
            
            # Get entries
            entries = []
            for entry in path.iterdir():
                if not include_hidden and entry.name.startswith('.'):
                    continue
                
                stat = entry.stat()
                entries.append({
                    "name": entry.name,
                    "path": str(entry.relative_to(WORKSPACE_ROOT)) if WORKSPACE_ROOT else str(entry),
                    "is_dir": entry.is_dir(),
                    "is_file": entry.is_file(),
                    "size": stat.st_size if entry.is_file() else None,
                    "modified": stat.st_mtime
                })
            
            # Sort: directories first, then files
            entries.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
            
            import json
            return json.dumps(entries, indent=2)
            
        except SecurityError:
            raise
        except Exception as e:
            raise IOError(f"Failed to list directory {dir_path}: {e}")
    
    def get_parameters(self) -> Dict[str, Any]:
        """Return tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to list",
                    "default": "."
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Include hidden files and directories",
                    "default": False
                }
            },
            "required": []
        }


class SecurityError(Exception):
    """Security violation exception."""
    pass


class FileHandlers:
    """Convenience wrapper class for file handlers."""
    
    def __init__(self, workspace_root: Optional[str] = None):
        self._read_handler = ReadFileTool(workspace_root)
        self._write_handler = WriteFileTool(workspace_root)
        self._edit_handler = EditFileTool(workspace_root)
        self._list_handler = ListDirTool(workspace_root)
    
    async def read_file(self, path: str, encoding: str = "utf-8") -> str:
        """Read file contents."""
        result = await self._read_handler.execute({"path": path, "encoding": encoding})
        return result
    
    async def write_file(self, path: str, content: str, mode: str = "w", encoding: str = "utf-8") -> str:
        """Write content to file."""
        result = await self._write_handler.execute({
            "path": path,
            "content": content,
            "mode": mode,
            "encoding": encoding
        })
        return result
    
    async def edit_file(self, path: str, find: str, replace: str, count: int = 1) -> str:
        """Edit file contents."""
        result = await self._edit_handler.execute({
            "path": path,
            "find": find,
            "replace": replace,
            "count": count
        })
        return result
    
    async def list_files(self, path: str = ".", recursive: bool = False, include_hidden: bool = False) -> str:
        """List directory contents."""
        result = await self._list_handler.execute({
            "path": path,
            "recursive": recursive,
            "include_hidden": include_hidden
        })
        return result
