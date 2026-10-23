import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional

model = None
tokenizer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, tokenizer
    # Load model here in real implementation
    model = "loading"
    yield
    model = None


app = FastAPI(lifespan=lifespan)


class HealthResponse(BaseModel):
    status: str


class InfoResponse(BaseModel):
    team: str
    model: str
    params: int
    max_seq_length: Optional[int] = None
    doc_stride: Optional[int] = None


class PredictRequest(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    context: str = Field(min_length=1, max_length=5000)
    question: str = Field(min_length=1, max_length=500)


class PredictResponse(BaseModel):
    id: str
    answer: Optional[str]
    start: Optional[int]
    score: float


def verify_token(authorization: Optional[str] = Header(None)):
    expected = os.environ.get("QA_API_TOKEN")
    if not expected:
        raise HTTPException(status_code=500, detail="Token not configured")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="unauthorized")
    token = authorization.split(" ", 1)[1]
    # constant-time not critical for scaffold but placeholder
    if token != expected:
        raise HTTPException(status_code=401, detail="unauthorized")
    return True


@app.get("/health")
async def health():
    if model == "loading":
        return JSONResponse(status_code=503, content={"status": "loading"})
    return {"status": "ok"}


@app.get("/info", response_model=InfoResponse)
async def info(authorized: bool = verify_token):
    return {
        "team": "Pistacho",
        "model": "distilbert-base-uncased",
        "params": 66362880,
        "max_seq_length": 384,
        "doc_stride": 128,
    }


@app.post("/predict", response_model=PredictResponse)
async def predict(req: PredictRequest, authorized: bool = verify_token):
    # Placeholder response
    return {
        "id": req.id,
        "answer": None,
        "start": None,
        "score": 0.0,
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    if exc.status_code in (400, 422):
        return JSONResponse(status_code=exc.status_code, content={"error": "bad_request", "detail": str(exc.detail)})
    return JSONResponse(status_code=exc.status_code, content={"error": "internal_error", "detail": str(exc.detail)})
