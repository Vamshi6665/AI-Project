# Clinical AI - Intelligent PDF Extraction Platform

Upload a clinical PDF, get validated structured JSON (patient, encounter, diagnoses, medications,
labs, vitals, allergies, follow-up) rendered as cards and tables.

React + Chakra UI -> nginx -> FastAPI -> OpenAI gpt-oss-20b on an AWS SageMaker endpoint.
Synthetic test documents only (`samples/`). No real patient data.

## Run locally in 5 minutes (mock mode, no keys)

```bash
# 1. Backend
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env
pytest -q                                              # 11 tests
uvicorn app.main:app --reload --port 8000              # Swagger: http://localhost:8000/api/docs

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev                                            # http://localhost:5173  (demo / demo123)

# 3. Sample PDFs (already generated; to regenerate)
python samples/generate_samples.py
```

## Switch the model

Edit `backend/.env`, restart the backend:

| LLM_PROVIDER | Needs | Use it for |
| --- | --- | --- |
| `mock` | nothing | UI work, tests |
| `openai` | `OPENAI_API_KEY` | Day 1 real-LLM testing |
| `sagemaker` | deployed endpoint + IAM | the real deployment |
| `bedrock` | Bedrock access to gpt-oss-20b | fallback if GPU quota is pending |

## Run with Docker (same as production)

```bash
docker compose up -d --build      # http://localhost
docker compose logs -f backend
docker compose down
```

## Deploy to AWS

1. `python infra/sagemaker/deploy_endpoint.py --role-arn <SageMaker execution role ARN>`
2. `python infra/sagemaker/test_endpoint.py`
3. Launch EC2 (Ubuntu 24.04, t3.medium) with the `clinical-ai-ec2-role` instance profile
4. On EC2: clone repo, `bash infra/ec2/setup_ubuntu.sh`, then `bash infra/ec2/make_env.sh`
   (writes `backend/.env` with a generated JWT secret and demo password; save the password it prints)
5. `docker compose up -d --build`
6. **When done for the day:** `python infra/sagemaker/delete_endpoint.py`

Full walkthrough: see the build guide doc.

## Layout

```
backend/app/
  main.py               app factory: middleware, routers, error handlers
  config.py             all settings from env vars
  security.py           JWT issue + validation
  errors.py             one error envelope for every failure
  middleware.py         request ID + access log
  logging_config.py     JSON logs
  schemas.py            Pydantic models (LLM output contract + API responses)
  routers/              /api/health, /api/auth/*, /api/extract, /api/extractions
  services/
    pdf_text.py         PDF -> text (PyMuPDF)
    prompts.py          system prompt with the JSON Schema embedded
    extractor.py        pipeline + JSON parsing + repair retry
    store.py            in-memory history (last 50)
    llm/                mock | openai | sagemaker | bedrock clients
frontend/src/
  api.js                axios client, token handling, error envelope
  App.jsx               layout + state
  components/           LoginForm, UploadPanel, HistoryList, ResultsView, EmptyState
infra/
  sagemaker/            deploy / test / delete the gpt-oss-20b endpoint
  iam/                  trust + least-privilege policies
  ec2/                  Ubuntu setup, redeploy script, Caddyfile for HTTPS
samples/                3 synthetic clinical PDFs + generator
```
