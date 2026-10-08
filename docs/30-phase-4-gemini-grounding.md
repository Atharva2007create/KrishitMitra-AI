# Phase 4 Gemini grounding

All SDK calls live behind `AIProvider`/`GeminiAIProvider`; routes and FAQ code do not call Gemini directly. The centrally configured primary stable Flash model is `gemini-3.8-flash`; `gemini-3.7-flash` is a same-provider availability fallback. Both remain configurable. Calls use bounded timeout/retries, low temperature, a token limit, and Pydantic structured output.

The invariant is question → safety classification → Phase 3 retrieval → sufficiency check → Gemini explanation → backend-owned citations. Gemini receives only farmer context, recent conversation, the question, and retrieved government chunks. It cannot select or invent citations. An insufficient result returns a localized safe message without invoking the model. Retrieval and model failures return `503`; the farmer question remains stored and no duplicate assistant message is created.

The policy treats question, history, and evidence as untrusted data, rejects hidden-prompt/credential disclosure, preserves numbers and warnings, and prohibits unsupported facts, diagnoses, current prices/weather, or unvalidated pesticide instructions.
