# Image-analysis design

## Frozen workflow

```mermaid
sequenceDiagram
  participant U as Farmer
  participant C as Web/Mobile
  participant API as FastAPI
  participant S3 as S3
  participant L as Lambda
  participant V as Gemini multimodal
  participant R as Official RAG
  U->>C: Capture or select image
  C->>C: Basic size/type/quality check
  C->>API: Request restricted upload
  API-->>C: Short-lived upload target + analysis ID
  C->>S3: Upload image
  C->>API: Submit object version/context
  API->>L: Start asynchronous workflow
  L->>V: Image + constrained observation schema
  V-->>L: Visual observations, uncertainty, quality limits
  L->>R: Retrieve approved applicable knowledge
  R-->>L: Evidence + identifiers
  L->>L: Evidence/safety/citation validation
  L->>API: Grounded result metadata
  API-->>C: Status/result + citations + limitations
```

## Output contract

The result separates:

1. `visual_observations`: visible color, shape, distribution, affected plant part, image-quality limitations; no disease certainty.
2. `possible_interpretations`: evidence-backed possibilities with uncertainty and alternatives.
3. `recommended_next_steps`: low-risk actions, requested additional evidence, or expert escalation.
4. `chemical_guidance`: absent unless current applicable official regulatory evidence supports every material detail.
5. `citations`, `limitations`, model/config version, and timestamps.

The UI must say “possible” or equivalent where appropriate and must never label a visual result as guaranteed diagnosis.

## Validation and state model

Client checks extension/declared type, size, and obvious capture quality. Server/S3 workflow independently checks actual format/decode, byte/pixel limits, checksum/object version, ownership, and safe key. States: `created → uploaded → queued → observing → retrieving → validating → completed`, with terminal `failed`, `rejected`, or `expired`. Retries are bounded and idempotent.

## Safety rules

- Gemini cannot independently invent pesticide name, dosage, rate, waiting period, or unsafe chemical action.
- Missing, stale, conflicting, or geographically/crop-inapplicable evidence yields a limitation/escalation.
- Low image quality, insufficient context, or ambiguous symptoms prompts safer recapture/context instructions.
- Relevant farm/crop-stage context is user-provided or stored; it is not inferred as fact from the image.
- Original image access is private and time-limited. Retention is configurable and disclosed.

## Open verification

Exact Gemini Flash model/schema, Lambda timeout/memory/event mechanism, malware/content inspection method, supported file types/limits, confidence presentation, agronomist review criteria, and deletion duration are finalized in Phase 5 after testing—not claimed in Phase 0.
