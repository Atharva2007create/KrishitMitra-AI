# Phase 5 crop-image analysis pipeline

1. An authenticated farmer requests a presigned JPEG, PNG or WebP upload.
2. The backend creates owner/session records and returns a private S3 POST for `farmer-uploads/{user_id}/{session_id}/{attachment_id}/{file_name}`.
3. Completion uses `HeadObject` to verify actual length, content type and signed attachment metadata.
4. S3 invokes `krishimitra-dev-image-analysis`; an authenticated analyze endpoint can safely re-invoke it.
5. Lambda revalidates bucket, key, metadata, size, MIME and magic bytes. Gemini receives a restricted visual-triage prompt.
6. Lambda writes an encrypted bounded result to `analysis-results/{attachment_id}.json`. `analysis-hashes/{model}/{sha256}.json` makes duplicate bytes/model idempotent.
7. The ownership-protected analysis endpoint synchronizes the result into `image_analyses`.
8. Guided assistance uses observations and candidate issues only to form a RAG query. Official evidence remains authoritative for guidance.

Statuses are `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`, and `IMAGE_INSUFFICIENT`. A blurry, dark, unrelated or crop-invisible image is not converted into a disease claim.

Lambda is limited to image quality, visible features, candidate issues with qualitative confidence, and follow-up questions. It must not provide a diagnosis, pesticide, dose, treatment or final guidance; treatment content is rejected. Exact pesticide instructions remain behind the regulatory gate.

The image bucket blocks public access, uses AES-256 encryption and expires development uploads after 30 days. IAM limits Lambda to upload/result/hash prefixes and the Gemini secret. Logs exclude image bytes, keys, farmer names and questions.
