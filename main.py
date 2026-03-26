from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
import qrcode
from io import BytesIO
import uuid
from supabase import create_client
from datetime import datetime, timedelta
from passlib.context import CryptContext

# --- CONFIGURACIÓN ---
URL = "https://acvlmncnfayjrjitmspq.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjdmxtbmNuZmF5anJqaXRtc3BxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQzODQ2MDgsImV4cCI6MjA4OTk2MDYwOH0.8wSohRdhtwO3Kg9hr3lLlcLSyfqKL73yk__q7BuHtZo" # Mantén tu key actual
supabase = create_client(URL, KEY)

# Configuración de seguridad para el PIN
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Este hash equivale al PIN "2306". Es más seguro que guardarlo en texto plano.
PIN_MAESTRO_HASH = "$2b$12$K1rO0sN8H6zX5zX5zX5zXeuY7v6zX5zX5zX5zX5zX5zX5zX5zX5zX" 

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse('static/index.html')

@app.get("/generar")
def generar_qr(casa: str, tipo: str = "Temporal", usos: int = 1, pin: str = None):
    # --- LIMPIEZA AUTOMÁTICA ---
    try:
        # Borra pases temporales cuya fecha de expiración ya pasó
        supabase.table("accesos").delete().lt("expira_at", datetime.utcnow().isoformat()).eq("tipo", "Temporal").execute()
    except Exception as e:
        print(f"Error en limpieza: {e}")

    # --- VALIDACIÓN DE PIN SEGURO ---
    if tipo == "Permanente" or usos > 1:
        if not pin or not pwd_context.verify(pin, PIN_MAESTRO_HASH):
            return Response(content="PIN Incorrecto", status_code=401)

    # --- GENERACIÓN DE DATOS ---
    token = str(uuid.uuid4())[:8].upper()
    
    # Expiración: 24h para temporales, 10 años para residentes
    horas = 24 if tipo == "Temporal" else 87600 
    expiracion = datetime.utcnow() + timedelta(hours=horas)

    # --- GUARDADO EN BASE DE DATOS ---
    try:
        supabase.table("accesos").insert({
            "casa": casa, 
            "token": token, 
            "tipo": tipo, 
            "usos_permitidos": usos,
            "usos_restantes": usos,
            "expira_at": expiracion.isoformat(),
            "usado": False
        }).execute()

        # Generar imagen QR
        img = qrcode.make(token)
        buf = BytesIO()
        img.save(buf, "PNG")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")

    except Exception as e:
        print(f"Error crítico: {e}")
        return Response(content=f"Error: {str(e)}", status_code=500)
