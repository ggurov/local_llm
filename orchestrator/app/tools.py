"""Tool implementations for the orchestrator."""

import json
import os
import subprocess
import tempfile
from typing import Any, Dict, List, Optional
from pathlib import Path

from .models import ToolResponse


class ToolRegistry:
    """Registry for available tools."""
    
    def __init__(self):
        self.tools = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools."""
        self.tools = {
            "get_map": self.get_map,
            "apply_patch": self.apply_patch,
            "search_logs": self.search_logs,
            "run_tests": self.run_tests,
            "file_operations": self.file_operations
        }
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get tool schemas for the LLM."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_map",
                    "description": "Fetch a table, map, or data structure by key",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                                "description": "The key to fetch"
                            }
                        },
                        "required": ["key"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "apply_patch",
                    "description": "Apply a code or data patch and run tests",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo": {
                                "type": "string",
                                "description": "Repository or project name"
                            },
                            "patch": {
                                "type": "string",
                                "description": "The patch to apply"
                            }
                        },
                        "required": ["repo", "patch"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_logs",
                    "description": "Search through log files for patterns",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "Search pattern or regex"
                            },
                            "log_path": {
                                "type": "string",
                                "description": "Path to log file or directory"
                            }
                        },
                        "required": ["pattern"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_tests",
                    "description": "Run unit tests for a project",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project_path": {
                                "type": "string",
                                "description": "Path to the project"
                            },
                            "test_pattern": {
                                "type": "string",
                                "description": "Test pattern to run"
                            }
                        },
                        "required": ["project_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "file_operations",
                    "description": "Perform file operations (read, write, list)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "operation": {
                                "type": "string",
                                "enum": ["read", "write", "list", "delete"],
                                "description": "File operation to perform"
                            },
                            "path": {
                                "type": "string",
                                "description": "File or directory path"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write (for write operation)"
                            }
                        },
                        "required": ["operation", "path"]
                    }
                }
            }
        ]
    
    async def execute_tool(
        self,
        tool_name: str,
        tool_call_id: str,
        arguments: Dict[str, Any]
    ) -> ToolResponse:
        """Execute a tool and return the response."""
        try:
            if tool_name not in self.tools:
                return ToolResponse(
                    tool_call_id=tool_call_id,
                    result=None,
                    error=f"Unknown tool: {tool_name}"
                )
            
            result = await self.tools[tool_name](**arguments)
            return ToolResponse(
                tool_call_id=tool_call_id,
                result=result,
                error=None
            )
        except Exception as e:
            return ToolResponse(
                tool_call_id=tool_call_id,
                result=None,
                error=str(e)
            )
    
    async def get_map(self, key: str) -> Dict[str, Any]:
        """Get a map/table by key (mock implementation)."""
        # This is a mock implementation - replace with actual data retrieval
        mock_data = {
            "boost_target": {
                "anomalies": [
                    {"id": 1, "type": "pressure_drop", "severity": "high"},
                    {"id": 2, "type": "temperature_spike", "severity": "medium"}
                ],
                "status": "active",
                "last_updated": "2024-01-15T10:30:00Z"
            },
            "engine_params": {
                "rpm": 2500,
                "temperature": 85,
                "pressure": 2.3
            }
        }
        
        if key in mock_data:
            return {"key": key, "data": mock_data[key]}
        else:
            return {"key": key, "data": None, "error": "Key not found"}
    
    async def apply_patch(self, repo: str, patch: str) -> Dict[str, Any]:
        """Apply a patch to a repository (mock implementation)."""
        # This is a mock implementation - replace with actual patch application
        return {
            "repo": repo,
            "patch_applied": True,
            "changes": ["file1.py", "file2.py"],
            "tests_passed": True,
            "message": "Patch applied successfully"
        }
    
    async def search_logs(self, pattern: str, log_path: Optional[str] = None) -> Dict[str, Any]:
        """Search through log files."""
        # Mock implementation - replace with actual log search
        return {
            "pattern": pattern,
            "matches": [
                {"file": "app.log", "line": 123, "content": f"Found: {pattern}"},
                {"file": "error.log", "line": 45, "content": f"Error: {pattern}"}
            ],
            "total_matches": 2
        }
    
    async def run_tests(self, project_path: str, test_pattern: Optional[str] = None) -> Dict[str, Any]:
        """Run tests for a project."""
        # Mock implementation - replace with actual test execution
        return {
            "project_path": project_path,
            "tests_run": 15,
            "tests_passed": 14,
            "tests_failed": 1,
            "duration": "2.3s",
            "status": "partial_success"
        }
    
    async def file_operations(
        self,
        operation: str,
        path: str,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform file operations."""
        try:
            path_obj = Path(path)
            
            if operation == "read":
                if not path_obj.exists():
                    return {"error": f"File not found: {path}"}
                with open(path_obj, 'r') as f:
                    return {"content": f.read(), "size": path_obj.stat().st_size}
            
            elif operation == "write":
                if content is None:
                    return {"error": "Content required for write operation"}
                with open(path_obj, 'w') as f:
                    f.write(content)
                return {"message": f"File written: {path}", "size": len(content)}
            
            elif operation == "list":
                if not path_obj.exists():
                    return {"error": f"Path not found: {path}"}
                if path_obj.is_dir():
                    files = [f.name for f in path_obj.iterdir()]
                    return {"files": files, "count": len(files)}
                else:
                    return {"error": "Path is not a directory"}
            
            elif operation == "delete":
                if not path_obj.exists():
                    return {"error": f"File not found: {path}"}
                path_obj.unlink()
                return {"message": f"File deleted: {path}"}
            
            else:
                return {"error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            return {"error": str(e)}

