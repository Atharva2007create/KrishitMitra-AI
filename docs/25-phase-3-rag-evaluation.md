# Phase 3 retrieval evaluation

The versioned dataset at [`data/evaluation/phase3-retrieval.json`](../data/evaluation/phase3-retrieval.json) contains 60 retrieval-focused questions. Fifty positive questions are grounded in concepts present in the verified source inventory; ten negative questions cover another crop, unrelated equipment/technology, nonsense, prompt-like text and later-phase live services.

The dataset intentionally stores no invented answer text. Each row records question, expected topic, expected source where known, expected evidence concept, retrieved result and pass/fail. Results remain null until the live corpus and real Gemini embeddings exist.

Coverage includes crop overview, soil-health context, varieties, transplanting/sowing, spacing, irrigation, weeds, pests, diseases, seed-treatment evidence, processing and milling. Fertilizer, drainage, harvest and post-harvest are not marked covered unless the final ingested corpus actually contains suitable official evidence.

## Quality gates

- direct, paraphrased and Tur/Toor/Arhar/Red gram terminology queries;
- exact scientific/variety/pest/disease terms through lexical search;
- semantic retrieval through pgvector;
- metadata and inactive-version filtering;
- no-evidence behavior;
- complete citation chain;
- deterministic ingestion, embedding validation and duplicate tests;
- migrations from an empty pgvector-enabled PostgreSQL database.

English is the tested Phase 3 language. Gemini Embedding 2 is multilingual, but Hindi/Marathi retrieval quality must not be claimed until corpus and evaluation evidence exist in those languages.

## Execution status

All 60 cases were executed against the live 23-chunk corpus on 2026-10-08: 27 passed and 33 failed. The failures are retained in the versioned dataset and are concentrated in evidence expected from the TLS-blocked ICAR page, the OCR-review field guide, variety ranking, and negative-query sufficiency. This is a retrieval baseline, not an inflated AI-accuracy claim.
