import sys
import traceback
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

# наши модули
from trans.simple_parser import IndentBlockParser
from trans.code_generator import CppCodeGenerator
from trans.semantic_analyzer import SemanticError, SemanticAnalyzer
from trans.lexer import LexicalError

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
    allow_credentials=False,  # важно – иначе нужно указывать точный origin
    allow_methods=["*"],  # разрешаем POST, GET, OPTIONS
    allow_headers=["*"],
)


# ✅ ручной ответ на OPTIONS (некоторые браузеры требуют)
@app.options("/translate")
def options_translate():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )


# модели данных
class TranslateIn(BaseModel):
    code: str


class ErrorDetail(BaseModel):
    type: str  # "lexical", "syntax", "semantic", "runtime" и т.д.
    message: str
    line: Optional[int] = None  # номер строки, если известен


class TranslateOut(BaseModel):
    success: bool
    cpp: Optional[str] = None
    errors: Optional[List[ErrorDetail]] = None


@app.post("/translate", response_model=TranslateOut)
def translate(payload: TranslateIn):
    code = payload.code or ""
    errors = []

    try:
        parser = IndentBlockParser()
        program = parser.parse(code)

        # Semantic analysis - must pass before code generation
        analyzer = SemanticAnalyzer()
        analyzer.analyze(program)  # will raise SemanticError if errors found

        # Only generate code if semantic analysis passed
        generator = CppCodeGenerator()
        cpp = generator.generate(program)

        return TranslateOut(success=True, cpp=cpp, errors=None)

    except LexicalError as le:
        line_num = getattr(le, "lineno", None)
        errors.append(
            ErrorDetail(
                type="lexical", message=getattr(le, "message", str(le)), line=line_num
            )
        )
    except SyntaxError as e:
        line_num = getattr(e, "lineno", None)
        if line_num is not None:
            try:
                line_num = int(line_num)
            except (ValueError, TypeError):
                line_num = None
        errors.append(ErrorDetail(type="syntax", message=str(e), line=line_num))
    except SemanticError as se:
        errors.extend(
            [
                ErrorDetail(type="semantic", message=msg)
                for msg in str(se).split("\n")
                if msg.strip()
            ]
        )
    except RecursionError:
        errors.append(
            ErrorDetail(
                type="runtime",
                message="Слишком глубокая рекурсия (возможно, левая рекурсия или бесконечный цикл)",
            )
        )
    except Exception as e:
        traceback.print_exc()
        errors.append(ErrorDetail(type="general", message=str(e)))

    return TranslateOut(success=False, cpp=None, errors=errors)


# health-check
@app.get("/health")
def health():
    return {"status": "ok"}
