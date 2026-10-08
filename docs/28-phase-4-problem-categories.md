# Phase 4 problem categories

Migration `20261008_0003` seeds 14 ordered, active V1 categories: sowing and seeds, soil and land, fertilizers and nutrients, irrigation and drainage, pests, diseases, crop symptoms, weeds, flowering and pods, harvesting, post-harvest, weather, market and selling, and other Tur problem.

Each row contains a stable code/slug, English/Hindi/Marathi title and description, icon key, display order, active flag, live-data flag, and a JSON `rag_topics` list reusing the Phase 3 taxonomy. Weather and market categories are present for navigation but marked as requiring live data where appropriate.

Authenticated reads use:

- `GET /api/v1/problem-categories?language=en|hi|mr`
- `GET /api/v1/problem-categories/{slug}?language=en|hi|mr`

Responses are mobile-sized and omit internal metadata, embeddings, and source-document contents.
