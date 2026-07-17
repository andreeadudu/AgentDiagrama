"""
Mermaid File Export Tool.

Saves a validated Mermaid diagram to a .mmd file on disk so the
user can open it directly in VS Code (with the Mermaid Preview
extension), share it, or include it in documentation.
"""

import os

from .tool import Tool

EXPORT_DIR = "exported_diagrams"


def export_mermaid_to_file(diagram_code: str, filename: str):
    """
    Saves Mermaid code to a .mmd file in the exported_diagrams/
    directory.

    Returns a dict with:
        success: bool
        file_path: str
        message: str
    """
    stripped = diagram_code.strip()

    if not stripped:
        return {
            "success": False,
            "file_path": "",
            "message": "Cannot export an empty diagram."
        }

    # Sanitize filename: keep only alphanumeric, hyphens, underscores.
    safe_name = "".join(
        c if c.isalnum() or c in "-_" else "_"
        for c in filename
    )

    if not safe_name:
        safe_name = "diagram"

    if not safe_name.endswith(".mmd"):
        safe_name += ".mmd"

    os.makedirs(EXPORT_DIR, exist_ok=True)
    file_path = os.path.join(EXPORT_DIR, safe_name)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(stripped + "\n")
    except OSError as e:
        return {
            "success": False,
            "file_path": "",
            "message": f"Failed to write file: {e}"
        }

    return {
        "success": True,
        "file_path": file_path,
        "message": f"Diagram saved to {file_path}"
    }


export_mermaid_to_file_tool = Tool(
    name="export_mermaid_to_file",
    description=(
        "Saves a Mermaid diagram to a .mmd file on disk. The file can "
        "be opened in VS Code with the Mermaid Preview extension, or "
        "included in project documentation. Use this when the user asks "
        "to save, export, or download a generated diagram."
    ),
    parameters={
        "type": "object",
        "properties": {
            "diagram_code": {
                "type": "string",
                "description": "The full Mermaid diagram code to save."
            },
            "filename": {
                "type": "string",
                "description": "Desired filename (without path). Example: "
                               "'login_flow' or 'microservice_architecture'."
            }
        },
        "required": ["diagram_code", "filename"]
    },
    callback=export_mermaid_to_file
)