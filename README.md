# NEON THREAD 🧥
Tienda de ropa de invierno con login futurista.

## Correr local
```bash
pip install -r requirements.txt
python app.py
```
Abre: http://localhost:5000

## Deploy en Render
1. Sube este repo a GitHub
2. Conecta en render.com → New Web Service
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
