from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import qrcode
from io import BytesIO
import uuid
from supabase import create_client

# --- CONEXIÓN A TU BASE DE DATOS ---
# (Copia estos datos de Supabase > Settings > API)
URL = "https://acvlmncnfayjrjitmspq.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjdmxtbmNuZmF5anJqaXRtc3BxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQzODQ2MDgsImV4cCI6MjA4OTk2MDYwOH0.8wSohRdhtwO3Kg9hr3lLlcLSyfqKL73yk__q7BuHtZo"
supabase = create_client(URL, KEY)

app = FastAPI()

# Esto sirve para que tu página web (HTML) se vea bien
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse('static/index.html')

@app.get("/generar/{casa}")
def generar_qr(casa: str):
    # 1. Creamos un código secreto único (Token)
    token_secreto = str(uuid.uuid4())[:8].upper()
    
    # 2. Guardamos en la tabla 'accesos' que acabas de crear
    # Por defecto lo creamos como 'Temporal'
    nuevo_registro = {
        "casa": casa, 
        "token": token_secreto, 
        "tipo": "Temporal", 
        "usado": False
    }
    supabase.table("accesos").insert(nuevo_registro).execute()
    
    # 3. Convertimos ese código secreto en un código QR
    img = qrcode.make(token_secreto)
    buf = BytesIO()
    img.save(buf)
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="image/png")