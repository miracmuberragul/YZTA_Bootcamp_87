from fastapi import FastAPI

app = FastAPI(title='Document Service')

@app.get('/health')
def health():
    return {'status': 'ok'}
