from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
import qrcode
from io import BytesIO
import uuid
from supabase import create_client
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
URL = "https://acvlmncnfayjrjitmspq.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjdmxtbmNuZmF5anJqaXRtc3BxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQzODQ2MDgsImV4cCI6MjA4OTk2MDYwOH0.8wSohRdhtwO3Kg9hr3lLlcLSyfqKL73yk__q7BuHtZo"
supabase = create_client(URL, KEY)

# Tu PIN para generar pases (Cámbialo si quieres otro)
PIN_MAESTRO = "2306" 

app = FastAPI()

# Esto sirve para que Render encuentre tu index.html
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse('static/index.html')

@app.get("/generar")
def generar_qr(casa: str, tipo: str = "Temporal", usos: int = 1, pin: str = None):
    # 1. Limpieza automática de pases viejos para que no se llene tu base de datos
    try:
        ahora = datetime.utcnow().isoformat()
        supabase.table("accesos").delete().lt("expira_at", ahora).eq("tipo", "Temporal").execute()
    except Exception as e:
        print(f"Error en limpieza: {e}")

    # 2. Validación de PIN (Solo pide PIN si es Residente o tiene más de 1 uso)
    if tipo == "Permanente" or int(usos) > 1:
        if pin != PIN_MAESTRO:
            return Response(content="PIN Incorrecto", status_code=401)

    # 3. Generación del Token y Expiración
    token = str(uuid.uuid4())[:8].upper()
    
    # 24 horas para invitados, 10 años para residentes
    horas = 24 if tipo == "Temporal" else 87600 
    expiracion = datetime.utcnow() + timedelta(hours=horas)

    # 4. Guardado en Supabase
    try:
        supabase.table("accesos").insert({
            "casa": casa, 
            "token": token, 
            "tipo": tipo, 
            "usos_permitidos": int(usos),
            "usos_restantes": int(usos),
            "expira_at": expiracion.isoformat(),
            "usado": False
        }).execute()

        # 5. Crear la imagen del QR
        img = qrcode.make(token)
        buf = BytesIO()
        img.save(buf, "PNG")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")

    except Exception as e:
        print(f"Error crítico: {e}")
        return Response(content=f"Error: {str(e)}", status_code=500)