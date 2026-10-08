# Phase 4 grounded FAQ system

`faq_items` stores canonical and localized questions/answers. `faq_citations` links every factual FAQ to active Phase 3 chunks and source documents. The read API joins through approved, active government sources and completed, active documents; if that chain becomes invalid it returns `409` instead of serving an unsupported answer.

FAQ generation is controlled rather than request-time. Run `python -m app.faq.cli generate --category <slug>` to create/update drafts, inspect them, then add `--activate` only for approved output. The workflow retrieves official evidence before Gemini, validates structured English/Hindi/Marathi output and numeric tokens, replaces citation links atomically, and skips questions with insufficient evidence.

Run `python -m app.faq.cli audit` after generation or a source-status change. It reports exact active/total counts by category and exits unsuccessfully if an active FAQ has missing translations or no valid active citation chain.

Reads use `GET /api/v1/problem-categories/{slug}/faqs` and `GET /api/v1/faqs/{id}` with an optional `language` query. Some categories intentionally have no FAQ until the Phase 3 corpus supports one; no target count overrides evidence quality.
