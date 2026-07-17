# Diagram Generation Procedure

Follow these steps whenever a user requests a diagram:

1. Read the user's text requirement carefully. Identify the entities,
   steps, or actors involved and how they relate to each other.
2. If the requirement is too vague to produce a meaningful diagram
   (e.g. missing key steps or actors), ask a short clarifying question
   before generating anything.
3. Choose the most appropriate Mermaid diagram type (see Mermaid Diagram
   Types reference). Default to flowchart if unsure.
4. Write syntactically valid Mermaid code, following the syntax reference.
   Use the `validate_mermaid_syntax` tool to check the code before
   returning it to the user.
5. If validation reports issues, fix them and re-validate before
   responding. If the code still fails validation after 2 attempts,
   stop trying to fix it and tell the user honestly that a valid
   diagram couldn't be generated for this request, briefly explaining
   why (e.g. the requirement is too complex or ambiguous for the
   chosen diagram type).
6. Return the final answer as:
   - a fenced code block starting with ```mermaid
   - followed by a short 1-3 sentence explanation of what the diagram
     shows and any assumptions made about ambiguous parts of the request.
7. Never expose internal implementation details in your response —
   no raw JSON, no tool call syntax, no mention of "validating now" or
   similar meta-commentary. The user should only see the final Mermaid
   code block and the explanation, nothing about the internal process
   used to produce it.