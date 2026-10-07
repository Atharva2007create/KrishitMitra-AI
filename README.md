# KrishiMitra AI

KrishiMitra AI is a planned government-evidence-backed farmer assistance platform. Version 1 is limited to Tur (pigeonpea) and supports responsive web, Android/iOS mobile, multilingual chat, source citations, crop-image assistance, weather, market, soil/nutrient context, and pesticide-regulatory validation.

This repository currently contains the **Phase 0 architecture and requirements freeze only**. It does not claim that application features, government integrations, AI integration, AWS infrastructure, database migrations, or performance results exist.

## Frozen stack

- Web: Next.js, TypeScript, Tailwind CSS, AWS Amplify
- Mobile: React Native, Expo, TypeScript
- API: Python, FastAPI, REST, Docker on Amazon EC2
- Data: Amazon RDS PostgreSQL with pgvector
- Storage and processing: Amazon S3 and AWS Lambda
- Authentication: Amazon Cognito
- AI: stable Gemini Flash-family model selected during implementation
- Monitoring: Amazon CloudWatch

## Architectural rule

Official or government evidence is the factual layer. Gemini may interpret, summarize, translate, and format retrieved evidence, but must not fabricate agricultural recommendations when sufficient trusted evidence is unavailable.

## Documentation

Start with [Project scope](docs/00-project-scope.md), [requirements](docs/01-requirements.md), and [system architecture](docs/02-system-architecture.md). The complete Phase 0 index is in [`docs/`](docs/).

## Status

Phase 0 documentation baseline. Phase 1 has not started.
