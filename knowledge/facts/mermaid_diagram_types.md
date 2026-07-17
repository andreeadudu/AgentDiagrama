# Mermaid Diagram Types — Quick Reference

Mermaid supports several diagram types. Pick the one that best fits the
user's request:

- **flowchart** — processes, decision trees, general workflows.
  Syntax starts with `flowchart TD` (top-down) or `flowchart LR` (left-right).
- **sequenceDiagram** — interactions between actors/systems over time
  (e.g. API calls, service-to-service communication, login flows).
  Shows message order explicitly.
- **classDiagram** — object-oriented structure: classes, attributes,
  methods, relationships (inheritance, composition).
- **erDiagram** — database entity-relationship models: tables and their
  relationships (one-to-many, many-to-many).
- **stateDiagram-v2** — finite state machines: states and transitions
  triggered by events.

If the user's request doesn't clearly map to one type, default to
**flowchart** — it's the most general-purpose and forgiving.

This agent focuses on software architecture and system design diagrams.
Requests for project-management or reporting visuals (Gantt charts, user
journeys, pie charts) are outside its scope — see agent_identity.md.