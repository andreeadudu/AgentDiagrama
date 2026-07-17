from tools.validate_mermaid_tool import validate_mermaid_syntax

test_cases = [
    (
        "Valid flowchart",
        """flowchart TD
    A[Start] --> B{Decision}
    B -- Yes --> C[Do something]
    B -- No --> D[Do something else]"""
    ),
    (
        "Valid sequence diagram",
        """sequenceDiagram
    participant User
    participant Server
    User->>Server: Request
    Server-->>User: Response"""
    ),
    (
        "Missing diagram type declaration",
        """A[Start] --> B[End]"""
    ),
    (
        "Unbalanced brackets",
        """flowchart TD
    A[Start --> B[End]"""
    ),
    (
        "Empty diagram",
        ""
    ),
]

for name, code in test_cases:
    result = validate_mermaid_syntax(code)
    status = "VALID" if result["valid"] else "INVALID"
    print(f"[{status}] {name}")
    if result["issues"]:
        for issue in result["issues"]:
            print(f"   - {issue}")
    print()