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
    # SEGURIDAD: Solo el dueño puede crear pases Permanentes o de muchos usos
    PIN_MAESTRO = "2306"  # <--- CAMBIA TU CONTRASEÑA AQUÍ

# Calculamos la expiración (24 horas para temporales, 10 años para permanentes)
    horas = 24 if tipo == "Temporal" else 87600 
    expiracion = datetime.utcnow() + timedelta(hours=horas)

    try:
        supabase.table("accesos").insert({
            "casa": casa, 
            "token": token, 
            "tipo": tipo, 
            "usos_permitidos": usos,
            "usos_restantes": usos,
            "expira_at": expiracion.isoformat(), # <--- Nueva columna
            "usado": False
        }).execute()
    
    if tipo == "Permanente" or usos > 1:
        if pin != PIN_MAESTRO:
            return Response(content="PIN Incorrecto", status_code=401)

    token = str(uuid.uuid4())[:8].upper()
    
    # Guardamos en Supabase (Asegúrate de haber creado las columnas en la tabla)
    try:
        supabase.table("accesos").insert({
            "casa": casa, 
            "token": token, 
            "tipo": tipo, 
            "usos_permitidos": usos,
            "usos_restantes": usos,
            "usado": False
        }).execute()

        img = qrcode.make(token)
        buf = BytesIO()
        img.save(buf, "PNG")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        return {"error": str(e)}