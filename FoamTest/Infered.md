# Inferred Facts Graph

```mermaid
graph TD;
    Corrosion -->|isCause| Crack;
    Corrosion -->|isCause| StressConcentration;
    Crack -->|isCause| Failure_Fatigue;
    Crack -->|isEffect| Corrosion;
    Failure_Fatigue -->|isEffect| Crack;
    StressConcentration -->|isEffect| Corrosion;

```
