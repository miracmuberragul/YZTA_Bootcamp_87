from fastapi import FastAPI

app = FastAPI(title='Chat Service')

@app.get('/health')
def health():
    return {'status': 'ok'}
