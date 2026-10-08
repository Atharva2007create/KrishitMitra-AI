# Phase 5 testing and acceptance

Automated Phase 5 coverage verifies:

- official-host SSRF protection and fail-closed authentication;
- IMD and AGMARKNET normalization with timestamps and provenance;
- stale-weather rejection and newest-first market ordering using actual arrival dates;
- source states that do not claim blocked integrations are live;
- image event rejection, byte-signature validation and size/type boundaries;
- rejection of treatment instructions from the visual model;
- attachment-scoped results and content-hash/model idempotency;
- authenticated ownership inherited from attachment and chat tests;
- migration upgrade/downgrade/upgrade and the full backend regression suite.

Cloud acceptance additionally requires a real private S3 upload, S3 event delivery, Gemini response, result synchronization, CloudWatch visibility, and a guided image-to-RAG answer backed by an official citation. These checks are reported separately from mock tests. External source acceptance remains `BLOCKED` while a source-owner credential is absent; mock tests never substitute for that live verification.
