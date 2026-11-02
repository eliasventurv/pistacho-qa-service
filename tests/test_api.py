import secrets
import time
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
import app as service

class FakePredictor:
    params=123
    config={'model':{'name':'distilbert-base-uncased','max_seq_length':384,'doc_stride':128}}
    def predict(self,context,question):
        if question=='fail': raise RuntimeError('private diagnostic')
        if question=='none': return {'answer':None,'start':None,'score':0.9}
        return {'answer':context[:1],'start':0,'score':0.8}

@pytest.fixture
def client(monkeypatch):
    token=secrets.token_urlsafe(24)
    monkeypatch.setenv('QA_API_TOKEN',token)
    monkeypatch.setattr(service,'load_predictor',lambda:FakePredictor())
    with TestClient(service.app,raise_server_exceptions=False) as c:
        for _ in range(100):
            if c.get('/health').status_code==200: break
            time.sleep(.01)
        c.headers['Authorization']='Bearer '+token
        yield c

@pytest.mark.parametrize('endpoint',['/info','/predict'])
@pytest.mark.parametrize('auth',[None,'Bearer wrong','bearer wrong','Basic wrong','Bearer '])
def test_auth(client,endpoint,auth):
    client.headers.pop('Authorization',None)
    headers={} if auth is None else {'Authorization':auth}
    response=client.get(endpoint,headers=headers) if endpoint=='/info' else client.post(endpoint,headers=headers,json={'id':'x','context':'abc','question':'q'})
    assert response.status_code==401
    assert response.json()=={'error':'unauthorized'}
    assert response.headers['www-authenticate']=='Bearer'

def test_info_health(client):
    assert client.get('/health').json()=={'status':'ok'}
    assert client.get('/info').json()['params']==123

@pytest.mark.parametrize('body',[
    {},{'id':'x','context':'abc'}, {'id':1,'context':'abc','question':'q'},
    {'id':'','context':'abc','question':'q'}, {'id':'x','context':'a'*5001,'question':'q'},
    {'id':'x','context':'abc','question':'q'*501},
    {'id':'x','context':'abc','question':'q','extra':True},
])
def test_invalid_body(client,body):
    r=client.post('/predict',json=body)
    assert r.status_code in (400,422)
    assert r.json()['error']=='bad_request'

def test_malformed_json(client):
    r=client.post('/predict',content='{',headers={'Content-Type':'application/json'})
    assert r.status_code==422 and r.json()['error']=='bad_request'

def test_unknown_route_uses_error_schema(client):
    r=client.get('/missing')
    assert r.status_code==404 and r.json()['error']=='bad_request'

@pytest.mark.parametrize('question',['q','none'])
def test_span_and_null(client,question):
    r=client.post('/predict',json={'id':'echo','context':'ábc','question':question})
    assert r.status_code==200
    p=r.json();assert p['id']=='echo'
    assert (p['answer'] is None)==(p['start'] is None)
    if p['answer'] is not None: assert 'ábc'[p['start']:p['start']+len(p['answer'])]==p['answer']

def test_failure_is_json(client):
    r=client.post('/predict',json={'id':'x','context':'abc','question':'fail'})
    assert r.status_code==500 and r.json()=={'error':'internal_error'}

def test_unloaded_not_healthy(client):
    service.app.state.predictor=None
    assert client.get('/health').status_code==503
    assert client.get('/health').json()=={'status':'loading'}

def test_missing_environment_fails_closed(client,monkeypatch):
    monkeypatch.delenv('QA_API_TOKEN')
    assert client.get('/info').status_code==500
    assert client.get('/health').status_code==503

def test_demo_page_is_public_html(client):
    del client.headers['Authorization']
    r=client.get('/')
    assert r.status_code==200 and 'text/html' in r.headers['content-type']
