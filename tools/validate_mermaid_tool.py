"""
Mermaid Syntax Validator Tool.

Performs a basic sanity check on Mermaid diagram code before it is
returned to the user, catching common syntax mistakes early.
"""

from .tool import Tool

VALID_DIAGRAM_KEYWORDS = [
    "flowchart", "sequenceDiagram", "classDiagram",
    "erDiagram", "stateDiagram-v2"
]


def validate_mermaid_syntax(diagram_code: str):
    """
    Runs basic structural checks on a block of Mermaid code.

    Returns a dict with:
        valid: bool
        issues: list[str]  (empty if valid)
    """
    issues = []
    stripped = diagram_code.strip()

    if not stripped:
        return {"valid": False, "issues": ["Diagram code is empty."]}

    first_line = stripped.splitlines()[0].strip()
    if not any(first_line.startswith(kw) for kw in VALID_DIAGRAM_KEYWORDS):
        issues.append(
            f"First line ('{first_line}') does not start with a known "
            f"diagram type keyword ({', '.join(VALID_DIAGRAM_KEYWORDS)})."
        )

    open_brackets = stripped.count("[") + stripped.count("{") + stripped.count("(")
    close_brackets = stripped.count("]") + stripped.count("}") + stripped.count(")")
    if open_brackets != close_brackets:
        issues.append(
            f"Unbalanced brackets: {open_brackets} opening vs "
            f"{close_brackets} closing."
        )

    return {"valid": len(issues) == 0, "issues": issues}


validate_mermaid_tool = Tool(
    name="validate_mermaid_syntax",
    description=(
        "Validates a block of Mermaid diagram code for basic structural "
        "correctness (diagram type declared, balanced brackets). Use this "
        "before returning a generated diagram to the user."
    ),
    parameters={
        "type": "object",
        "properties": {
            "diagram_code": {
                "type": "string",
                "description": "The full Mermaid diagram code to validate."
            }
        },
        "required": ["diagram_code"]
    },
    callback=validate_mermaid_syntax
)