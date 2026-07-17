# Mermaid Syntax Reference

## Flowchart

Direction: `flowchart TD` (top-down), `LR` (left-right), `BT`, `RL`.

Node shapes:
- `A[Rectangle text]` — process step
- `B(Rounded rectangle)` — start/end-ish softer step
- `C{Decision}` — branching/conditional
- `D((Circle))` — connector or event
- `E[[Subroutine]]` — predefined process
- `F[(Database)]` — data store

Arrows:
- `A --> B` — solid arrow (flow)
- `A -.-> B` — dotted arrow (optional/conditional flow)
- `A ==> B` — thick arrow (emphasis)
- `A -- label --> B` or `A -->|label| B` — labeled arrow

Subgraphs (grouping):
```
subgraph Group1[Optional Title]
  A --> B
end
```

Styling:
- `classDef highlight fill:#f9f,stroke:#333,stroke-width:2px;` — define a reusable style
- `class A,B highlight` — apply a style to one or more nodes

## Sequence Diagram

Declaring participants (optional, auto-created on first message):
- `participant Alice`
- `actor Bob` — rendered as a stick figure instead of a box

Messages:
- `A->>B: message` — solid arrow, synchronous call
- `A-->>B: message` — dashed arrow, reply/return
- `A-)B: message` — async message, open arrowhead

Activation (lifeline highlighting):
- `activate B` / `deactivate B`, or shorthand `A->>+B: msg` ... `B-->>-A: reply`

Notes:
- `Note right of A: text`, `Note left of A: text`, `Note over A,B: text`

Control blocks:
```
loop every day
  A->>B: check status
end
alt success
  A->>B: confirm
else failure
  A->>B: retry
end
```

## Class Diagram

Class declaration:
```
class Animal {
  +String name
  +int age
  +makeSound()
}
```

Visibility modifiers: `+` public, `-` private, `#` protected, `~` package.

Relationships:
- `A --|> B` — inheritance
- `A --* B` — composition
- `A --o B` — aggregation
- `A --> B` — association
- `A ..> B` — dependency
- `A ..|> B` — realization (interface implementation)

Cardinality on relationships: `A "1" --> "many" B`

## ER Diagram

```
CUSTOMER ||--o{ ORDER : places
ORDER ||--|{ LINE-ITEM : contains
```

Cardinality symbols: `||` exactly one, `o|` zero or one, `}o` zero or many, `}|` one or many.

Entity attributes:
```
CUSTOMER {
  string name
  string id PK
}
```

## State Diagram (stateDiagram-v2)

```
stateDiagram-v2
  [*] --> Idle
  Idle --> Running : start
  Running --> Idle : stop
  Running --> [*]
```

`[*]` denotes the initial/final pseudo-state. Composite (nested) states:
```
state Running {
  [*] --> Processing
  Processing --> Done
}
```
