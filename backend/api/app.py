import sys
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# наши модули
from trans.simple_parser import IndentBlockParser
from trans.code_generator import CppCodeGenerator

# увеличиваем лимит рекурсии (временно)
sys.setrecursionlimit(5000)

# создаём приложение
app = FastAPI(title="Translator API", version="1.0.0")

# ✅ CORS – чтобы фронтенд мог отправлять OPTIONS/POST без 405
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,           # важно — иначе нужно указывать точный origin
    allow_methods=["*"],               # разрешаем POST, GET, OPTIONS
    allow_headers=["*"],
)

# ✅ ручной ответ на OPTIONS (некоторые браузеры требуют)
@app.options("/translate")
def options_translate():
    return Response(status_code=200, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    })


# модели данных
class TranslateIn(BaseModel):
    code: str


class TranslateOut(BaseModel):
    cpp: str


# ✅ основной endpoint
@app.post("/translate", response_model=TranslateOut)
def translate(payload: TranslateIn):
    code = payload.code or ""
    try:
        parser = IndentBlockParser()
        program = parser.parse(code)

        generator = CppCodeGenerator()
        cpp = generator.generate(program)

        return {"cpp": cpp}

    except RecursionError:
        raise HTTPException(
            status_code=400,
            detail=(
                "Слишком глубокая рекурсия в парсере или генераторе. "
                "Проверьте: левую рекурсию, парсер, AST, циклы."
            )
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# health-check
@app.get("/health")
def health():
    return {"status": "ok"}
