from datetime import datetime, timedelta
from fastapi import FastAPI, Response, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
import qrcode
from io import BytesIO
import uuid
from supabase import create_client

# --- CONFIGURACIÓN ---
URL = "https://acvlmncnfayjrjitmspq.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjdmxtbmNuZmF5anJqaXRtc3BxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQzODQ2MDgsImV4cCI6MjA4OTk2MDYwOH0.8wSohRdhtwO3Kg9hr3lLlcLSyfqKL73yk__q7BuHtZo" 
supabase = create_client(URL, KEY)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse('static/index.html')

@app.get("/generar")
def generar_qr(
    casa: str, 
    tipo: str = "Temporal", 
    usos: int = 1, 
    pin: str = None
):
    # 1. SEGURIDAD: Validar primero si tiene permiso
    PIN_MAESTRO = "2306" 
    
    if tipo == "Permanente" or usos > 1:
        if pin != PIN_MAESTRO:
            return Response(content="PIN Incorrecto", status_code=401)

    # 2. GENERACIÓN DE DATOS: Crear el token y las fechas
    token = str(uuid.uuid4())[:8].upper()
    
    # Calculamos la expiración (24h para temporales, 10 años para permanentes)
    horas = 24 if tipo == "Temporal" else 87600 
    expiracion = datetime.utcnow() + timedelta(hours=horas)

    # 3. BASE DE DATOS: Guardar todo en un solo bloque try/except
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

        # 4. IMAGEN: Crear el QR solo si se guardó bien en la base de datos
        img = qrcode.make(token)
        buf = BytesIO()
        img.save(buf, "PNG")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")

    except Exception as e:
        print(f"Error crítico: {e}")
        return {"error": str(e)}