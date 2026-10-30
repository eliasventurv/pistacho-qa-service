"""Contract-compliant CPU serving. No remote inference."""
import asyncio
import hmac
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

def load_predictor():
    import torch
    from src.predict import QAPredictor
    torch.set_num_threads(int(os.environ.get('QA_CPU_THREADS', '4')))
    return QAPredictor(device='cpu')

@asynccontextmanager
async def lifespan(app):
    app.state.predictor = None
    app.state.load_error = False
    app.state.inference_lock = asyncio.Lock()
    async def load():
        try:
            app.state.predictor = await run_in_threadpool(load_predictor)
        except Exception:
            app.state.load_error = True
            logger.exception('Model could not be loaded')
    task = asyncio.create_task(load())
    yield
    await task
    app.state.predictor = None

app = FastAPI(title='Pistacho QA', lifespan=lifespan)

class PredictRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    id: str = Field(min_length=1, max_length=64)
    context: str = Field(min_length=1, max_length=5000)
    question: str = Field(min_length=1, max_length=500)

class PredictResponse(BaseModel):
    id: str
    answer: Optional[str]
    start: Optional[int] = Field(ge=0)
    score: float = Field(ge=0, le=1)

def verify_token(authorization: Optional[str] = Header(None)):
    expected = os.environ.get('QA_API_TOKEN')
    if not expected:
        raise HTTPException(500, 'QA_API_TOKEN is not configured')
    if not authorization or not authorization.startswith('Bearer ') or not hmac.compare_digest(
            authorization[7:].encode('utf-8'), expected.encode('utf-8')):
        raise HTTPException(401, 'unauthorized', headers={'WWW-Authenticate': 'Bearer'})

def get_predictor(request):
    predictor = getattr(request.app.state, 'predictor', None)
    if predictor is None:
        raise HTTPException(500, 'Model is unavailable')
    return predictor

@app.get('/health')
async def health(request: Request):
    ready = getattr(request.app.state, 'predictor', None) is not None and bool(os.environ.get('QA_API_TOKEN'))
    return JSONResponse({'status': 'ok' if ready else 'loading'}, status_code=200 if ready else 503)

@app.get('/info', dependencies=[Depends(verify_token)])
async def info(request: Request):
    predictor = get_predictor(request)
    cfg = predictor.config['model']
    return {'team': 'Pistacho', 'model': cfg['name'], 'params': predictor.params,
            'max_seq_length': cfg['max_seq_length'], 'doc_stride': cfg['doc_stride']}

@app.post('/predict', response_model=PredictResponse, dependencies=[Depends(verify_token)])
async def predict(req: PredictRequest, request: Request):
    predictor = get_predictor(request)
    async with request.app.state.inference_lock:
        result = await run_in_threadpool(predictor.predict, req.context, req.question)
    return {'id': req.id, **result}

@app.exception_handler(HTTPException)
async def http_error(request, exc):
    code = 'unauthorized' if exc.status_code == 401 else 'bad_request' if exc.status_code in (400,422) else 'internal_error'
    return JSONResponse({'error': code}, status_code=exc.status_code, headers=exc.headers)

@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse({'error': 'bad_request', 'detail': 'Body must match PredictRequest.'}, status_code=422)

@app.exception_handler(Exception)
async def internal_error(request, exc):
    logger.error('Request failed', exc_info=(type(exc), exc, exc.__traceback__))
    return JSONResponse({'error': 'internal_error'}, status_code=500)
