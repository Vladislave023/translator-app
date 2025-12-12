# Translator App

FastAPI + React

## Быстрый старт (Dev)

```bash
# backend
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.app:app --reload --port 8000

# frontend
cd ../frontend/translator-frontend
npm install
npm start  # откроется http://localhost:3000
```

Фронтенд отправляет запросы на `http://localhost:8000` (см. `src/services/api.js`).
