# Project scope

## Frozen purpose

KrishiMitra AI V1 provides reliable, understandable, source-backed assistance for **Tur (pigeonpea)** farmers. It uses approved official/government material as factual evidence and uses AI to interpret and communicate that evidence.

## V1 users

### Farmer

May authenticate by phone OTP; choose Marathi, Hindi, or English; manage a profile, farms, and a current Tur crop cycle; ask questions; inspect citations; upload/capture crop images; view weather and mandi information; review chat history; submit feedback; and manage basic account settings.

### Administrator

Authenticates by email/password and an administrator role. May inspect/manage source metadata, source-document state, ingestion jobs and failures, feedback, flagged responses, user/system summaries, and health/audit information. An administrator may disable a bad or superseded source version. V1 defines no additional role.

## V1 modules

1. Registration and authentication
2. Farmer profile, farm, and Tur crop-cycle management
3. Multilingual AI chat and history
4. Government-backed hybrid RAG and citations
5. Image upload/capture and crop-image assistance
6. Weather information and advisories
7. Tur mandi/market information
8. Soil/nutrient context
9. Pesticide regulatory validation
10. Feedback
11. Admin/data-source management
12. Monitoring and audit support

## Success boundary

The product should be functionally representative of a real system, but Phase 0 sets contracts only. A later release must refuse or qualify answers when evidence is missing, stale, geographically inapplicable, or insufficient. Image output is an observation and evidence-backed interpretation, never a guaranteed diagnosis.

## Non-goals

No IoT control, drones, blockchain, autonomous machinery, Kubernetes, premature microservices, all-crop support, large-scale custom computer-vision pipeline, or separate backend per client. Phase 0 includes no application code, migrations, embeddings, source ingestion, AWS provisioning, or deployment.

## Confirmed versus unresolved

Confirmed: stack, two roles, three V1 languages, Tur-only initial crop, common FastAPI backend, six source groups, evidence-before-generation, and AWS service responsibilities.

External verification required: precise availability/licensing/access method for each source; stable Gemini and embedding model identifiers; Cognito SMS delivery configuration and cost; precise retention durations; weather/market refresh SLAs; and quantitative quality thresholds.
