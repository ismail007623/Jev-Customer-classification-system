# SupportFlow AI — Backend

FastAPI backend with LangGraph orchestration, Jev classification, and OpenAI response generation.

## Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
```

## Run

```bash
python -m app.main
```

- API: http://localhost:8080
- Swagger: http://localhost:8080/docs

## Environment Variables

See `.env.example` for all required variables.
