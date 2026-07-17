"""
General-purpose utilities, reusable in any component of the application.
"""

import tiktoken

# cl100k_base is the encoding used by gpt-3.5 / gpt-4 and works as a
# good general-purpose proxy for any model, including local models
# (e.g. Ollama-hosted ones) that don't have their own encoding
# registered in tiktoken.
DEFAULT_ENCODING = "cl100k_base"


def count_tokens(text: str, encoding_name: str = DEFAULT_ENCODING) -> int:
    """
    Returns the number of tokens in a text, using tiktoken.
    """
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


if __name__ == "__main__":
    sample_texts = [
        "Draw a flowchart.",
        "Generate a sequence diagram for the login flow between the client, the auth service and the database.",
        "You are Diagrama, a diagram generation assistant. " * 5,
    ]

    for text in sample_texts:
        print(f"{count_tokens(text)} tokens  ->  {text[:60]!r}")