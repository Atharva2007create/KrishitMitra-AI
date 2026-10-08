# Phase 3 government data

## Trust boundary

Phase 3 accepts agricultural evidence only from public HTTPS resources on official ICAR (`icar.gov.in`) and ICAR-IIPR (`icar-iipr.org.in`) hosts. Redirects are revalidated against the same allowlist. Blogs, commercial pages, mirrors, forums, social media, and generated content are rejected by the acquisition layer.

The machine-readable inventory is [`data/sources/phase3-icar-pigeonpea.json`](../data/sources/phase3-icar-pigeonpea.json). A null publication date is intentional when the official page does not expose a verifiable date. The pipeline calculates SHA-256 from downloaded bytes and records the checksum only after acquisition.

## V1 source audit

| Organization | Official publication/page | Format | Audit status | Candidate chunks | Intended coverage |
|---|---|---|---|---:|---|
| ICAR | Transplanting Technology in Bidar District | HTML advisory | `BLOCKED_OFFICIAL_TLS_CERTIFICATE` | — | transplanting, production evidence |
| ICAR-IIPR | A Field Guide for Pests and Diseases of Pigeonpea | PDF | `REQUIRES_OCR_REVIEW` | — | pest and disease identification/management |
| ICAR-IIPR | Pigeonpea Crop Overview | HTML | `COMPLETED` | 1 | crop overview and soil-health context |
| ICAR-IIPR | Pigeonpea Varieties | HTML | `COMPLETED` | 6 | varieties, zones, duration and resistance traits |
| ICAR-IIPR | AICRP on Kharif Pulses — Pigeonpea Recommendations | HTML | `COMPLETED` | 14 | varieties, spacing, irrigation, pest/disease trials |
| ICAR-IIPR | Crop Production Technologies — Pigeonpea Evidence | HTML | `COMPLETED` | 2 | weed management and processing/milling |

The direct ICAR page currently presents an expired official TLS certificate, so the client refuses it instead of disabling certificate validation. The field guide is image-only in the tested extraction path and is held for explicit OCR quality review. The other four official ICAR-IIPR HTML pages were ingested on 2026-10-08.

Mixed-crop HTML pages use an explicit Pigeonpea/Tur/Arhar block filter. The original page is retained unchanged in S3; only relevant blocks enter active Pigeonpea chunks. This prevents knowledge about another pulse from being mislabeled as Tur.

## Storage and provenance

Original bytes are stored privately at `government/<organization>/pigeonpea/<document-id>/original.<ext>`. Extracted block JSON is stored separately at `processed/<document-id>/extracted.json`. S3 server-side encryption is requested on every object, and bucket public-access blocking and versioning remain controlled by the Phase 1 foundation stack.

Each active chunk resolves through `source_document_id` to the source document, organization, canonical public URL, checksum, version, retrieval timestamp, S3 evidence key, and page/section metadata. Private S3 keys are never returned by public source APIs.

The ICAR-IIPR pages contain dynamic markup whose raw download hash can change even when agricultural evidence does not. The pipeline therefore retains the exact raw SHA-256 as the immutable evidence checksum and separately calculates a stable normalized `knowledge_checksum` for same-URL idempotency. Two consecutive audits produced different raw hashes and identical knowledge checksums for all four ready pages.

## Version and activation rules

An identical organization plus SHA-256 is idempotent. A changed document at the same canonical URL creates a new document ID, preserves the prior row and S3 original, and links `supersedes_document_id`. The prior document and chunks become inactive only after extraction, embedding, and validation of the replacement succeed.

No document is marked ingested until its original has been stored, its chunks have valid real embeddings, and the database transaction has completed. The machine-readable inventory consequently leaves `checksum` and `chunk_count` null before live ingestion.
