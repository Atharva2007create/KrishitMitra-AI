# KrishiMitra AI

KrishiMitra AI is a government-evidence-backed farmer assistant. V1 is limited to Tur (pigeonpea). Phase 4 adds problem-first guided assistance, multilingual grounded FAQs, personalized Gemini Flash explanations with deterministic citations, and a secure attachment-upload foundation. Image diagnosis, live weather, live markets, and final UI remain out of scope.

## Architecture

Responsive Next.js web and React Native/Expo mobile clients share one versioned FastAPI REST backend. PostgreSQL with pgvector is used locally through Docker and later through Amazon RDS. AWS foundations use Amplify, EC2, RDS, S3, Cognito, Lambda, CloudWatch, IAM roles, and managed secrets as documented in [`docs/`](docs/README.md).

## Structure

```text
apps/web/                 Next.js + TypeScript + Tailwind status shell
apps/mobile/              Expo + React Native + TypeScript status shell
backend/                  FastAPI core API, Alembic migrations, security and tests
infrastructure/           CloudFormation and Lambda foundation source
scripts/                  Local database initialization
data/                     Verified source inventory and retrieval evaluation dataset
docs/                     Phase 0 contract plus Phase 1–4 guides
.github/workflows/        Non-deploying CI
docker-compose.yml        FastAPI + PostgreSQL/pgvector development stack
```

## Prerequisites

- Git
- Node.js 22 LTS and npm
- Python 3.12 or 3.13
- Docker Desktop with Compose
- Expo Go or an Android/iOS simulator for interactive mobile testing
- AWS CLI only for authorized infrastructure work

Copy `.env.example` to `.env` for local Docker overrides. Never commit `.env` or real credentials.

## Docker: backend and PostgreSQL

```powershell
docker compose up --build -d
curl.exe http://localhost:8000/health
curl.exe http://localhost:8000/api/v1/ready
docker compose exec db psql -U krishimitra -d krishimitra -c "SELECT version();"
docker compose exec db psql -U krishimitra -d krishimitra -c "SELECT extversion FROM pg_extension WHERE extname='vector';"
docker compose down
```

The named database volume persists across ordinary `down`. Do not use `down -v` unless intentionally deleting local development data.

## Backend without Docker

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
ruff check .
ruff format --check .
mypy app
pytest
```

`GET /health` is process health and does not require the database. `GET /api/v1/ready` checks PostgreSQL connectivity.

## Web

```powershell
cd apps/web
npm install
$env:NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"
npm run dev
```

Open `http://localhost:3000`. Quality checks: `npm run lint`, `npm run typecheck`, `npm test`, and `npm run build`.

## Mobile

```powershell
cd apps/mobile
npm install
$env:EXPO_PUBLIC_API_BASE_URL="http://YOUR-LAN-IP:8000"
npm start
```

`localhost` on a physical phone means the phone itself. Use the development computer's reachable LAN IP, allow only the necessary local firewall access, and keep both devices on an appropriate trusted network. Android emulators may use `10.0.2.2`; simulator behavior varies.

Validate without an emulator using `npm run lint`, `npm run typecheck`, `npm test`, and `npx expo config --type public`.

## AWS development

AWS creation and verification are recorded in [Phase 1 AWS resources](docs/14-phase-1-aws-resources.md) and the [Phase 2 testing record](docs/20-phase-2-testing.md). Never use the AWS root account. Chargeable EC2/RDS/Amplify/Cognito messaging resources require explicit inventory and cleanup awareness.

Deployed farmer web application: <https://main.d32qjrxuwdvdbd.amplifyapp.com>

Deployed admin console: <https://main.d32qjrxuwdvdbd.amplifyapp.com/admin>

Deployed API: <https://vruyoz5jo4.execute-api.ap-south-1.amazonaws.com/docs>

## Troubleshooting

- Backend offline in web/mobile: confirm Docker is healthy and the configured API URL is reachable.
- Readiness returns 503: start PostgreSQL and verify `DATABASE_URL`.
- Port collision: stop the conflicting local service or intentionally override published ports.
- npm cache permission errors: set `npm_config_cache` to a writable project-local temporary directory.
- Expo physical device cannot connect: replace `localhost` with the host LAN IP and verify network/firewall reachability.
- AWS command fails: verify `aws sts get-caller-identity`, region `ap-south-1`, IAM permissions, and never expose credentials in logs.

## Status

Phases 0–8 are implemented as a production-style college prototype. The final deployment, validation evidence, portability instructions, and residual limitations are recorded in the [Phase 8 finalization report](docs/39-phase-8-finalization.md).
