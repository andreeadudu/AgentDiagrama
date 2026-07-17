# Software Architecture Patterns — Quick Reference

Common architecture patterns a software architect might ask to diagram:

- **Layered (N-tier)** — presentation, business logic, data access, database.
  Typically a flowchart (TD) or class diagram showing layer dependencies.
- **Microservices** — independent services communicating via APIs or message
  queues. Best shown as a sequence diagram (service-to-service calls) or
  flowchart (overall topology).
- **Event-driven** — producers emit events, consumers react asynchronously.
  Sequence diagrams show event flow; state diagrams show how entities react
  to events.
- **Client-server** — client sends requests, server processes and responds.
  Sequence diagram is the natural fit.
- **MVC (Model-View-Controller)** — separation of concerns in a UI app.
  Class diagram for structure, sequence diagram for request lifecycle.
- **Repository / Data Access** — entities, repositories, database.
  ER diagram for the data model, class diagram for the code structure.
- **Pub/Sub (Publish-Subscribe)** — publishers send messages to a topic,
  subscribers receive them. Sequence diagram for message flow.
- **State Machine** — an entity transitions between states based on events
  or conditions. State diagram is the direct match.