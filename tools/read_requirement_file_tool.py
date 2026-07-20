"""
Requirement File Reader Tool.

Reads a plain-text file (.txt) containing a system description,
process specification, or design requirement, and returns its
content so the agent can generate a diagram from it.

Typical use case: a software architect has a design doc or RFC
written as a text file and wants to produce architecture diagrams
from it without manually retyping the content.
"""

import os

from .tool import Tool


def read_requirement_file(file_path: str):
    """
    Reads a .txt file from disk and returns its content.

    Returns a dict with:
        success: bool
        content: str
        message: str
    """
    if not file_path.strip():
        return {
            "success": False,
            "content": "",
            "message": "File path cannot be empty."
        }

    if not os.path.exists(file_path):
        return {
            "success": False,
            "content": "",
            "message": f"File not found: {file_path}"
        }

    if not file_path.endswith(".txt"):
        return {
            "success": False,
            "content": "",
            "message": f"Only .txt files are supported. Got: {file_path}"
        }

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
    except OSError as e:
        return {
            "success": False,
            "content": "",
            "message": f"Failed to read file: {e}"
        }

    if not content:
        return {
            "success": False,
            "content": "",
            "message": "File is empty."
        }

    return {
        "success": True,
        "content": content,
        "message": f"Successfully read {len(content)} characters from {file_path}"
    }


read_requirement_file_tool = Tool(
    name="read_requirement_file",
    description=(
        "Reads a plain-text (.txt) file containing a system description, "
        "process specification, or design requirement. Use this when the "
        "user provides a file path instead of typing the requirement "
        "directly. After reading, generate a diagram from the file content."
    ),
    parameters={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the .txt file to read."
            }
        },
        "required": ["file_path"]
    },
    callback=read_requirement_file
)
