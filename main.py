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

PIN_MAESTRO = "19728086" 

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse('static/index.html')

@app.get("/generar")
def generar_qr(casa: str, tipo: str = "Temporal", usos: int = 1, pin: str = None):
    try:
        ahora = datetime.utcnow().isoformat()
        supabase.table("accesos").delete().lt("expira_at", ahora).eq("tipo", "Temporal").execute()
    except Exception as e:
        print(f"Error en limpieza: {e}")

    # VALIDACIÓN:
    if tipo == "Permanente" or tipo == "ListaBlanca" or int(usos) > 2:
        if pin != PIN_MAESTRO:
            return Response(content="PIN Incorrecto", status_code=401)

    token = str(uuid.uuid4())[:8].upper()
    horas = 24 if tipo == "Temporal" else 87600 
    expiracion = datetime.utcnow() + timedelta(hours=horas)

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

        img = qrcode.make(token)
        buf = BytesIO()
        img.save(buf, "PNG")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")

    except Exception as e:
        print(f"Error crítico: {e}")
        return Response(content=f"Error: {str(e)}", status_code=500)

# --- NUEVA FUNCIÓN: ACTUALIZAR ESTATUS (LISTA NEGRA / PERDONAR) ---
@app.get("/actualizar_estatus")
def actualizar_estatus(casa: str, tipo: str, pin: str):
    # 1. Validar el PIN Maestro
    if pin != PIN_MAESTRO:
        return Response(content="PIN de seguridad incorrecto", status_code=401)

    try:
        # 2. Actualizar en Supabase el campo 'tipo' buscando por el nombre de la 'casa'
        # El .eq("casa", casa) buscará al residente que ya tiene ese nombre.
        res = supabase.table("accesos").update({"tipo": tipo}).eq("casa", casa).execute()

        if res.data:
            return Response(content=f"Residente {casa} actualizado a {tipo}", status_code=200)
        else:
            return Response(content="No se encontró un residente con ese nombre", status_code=404)

    except Exception as e:
        print(f"Error al actualizar estatus: {e}")
        return Response(content=f"Error en la base de datos: {str(e)}", status_code=500)
