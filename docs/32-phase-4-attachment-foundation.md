# Phase 4 attachment foundation

`message_attachments` records owner, session, optional message, attachment type, source (`UPLOAD`, `CAMERA`, or `DOCUMENT_PICKER`), name, MIME type, size, S3 key, and lifecycle status. Supported initiation types are JPEG/PNG/WebP images and PDF documents. The API validates ownership, basename, exact MIME allowlist, positive/configured size, and produces a short-lived S3 presigned POST constrained by content type, size, private owner-scoped key, and server-side encryption.

Endpoints are `POST /api/v1/attachments/upload`, `POST /api/v1/attachments/{id}/complete`, and `GET /api/v1/attachments/{id}`. IAM is limited to the `attachments/*` prefixes in the private image/document buckets. Completion marks the record `PENDING_ANALYSIS`; a text answer may explicitly say the attachment was not analyzed.

There is deliberately no Lambda trigger, image diagnosis, OCR, document interpretation, or Gemini multimodal call in Phase 4. Those operations remain Phase 5.
