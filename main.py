from fastapi.responses import StreamingResponse
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import qrcode
from io import BytesIO
import uuid
from supabase import create_client

# --- CONEXIÓN ---
URL = "https://acvlmncnfayjrjitmspq.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjdmxtbmNuZmF5anJqaXRtc3BxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQzODQ2MDgsImV4cCI6MjA4OTk2MDYwOH0.8wSohRdhtwO3Kg9hr3lLlcLSyfqKL73yk__q7BuHtZo" # Asegúrate de que sea tu llave completa
supabase = create_client(URL, KEY)

app = FastAPI()

# Montamos la carpeta para el diseño
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse('static/index.html')

@app.get("/generar/{casa}")
def generar_qr(casa: str):
    token = str(uuid.uuid4())[:8].upper()
    
    # Guardamos en Supabase
    try:
        supabase.table("accesos").insert({
            "casa": casa, 
            "token": token, 
            "tipo": "Temporal", 
            "usado": False
        }).execute()
    except Exception as e:
        print(f"Error: {e}")

    # Creamos el QR
    img = qrcode.make(token)
    buf = BytesIO()
    img.save(buf, "PNG")
    buf.seek(0) # Regresamos al inicio del archivo
    
    return StreamingResponse(buf, media_type="image/png")

    img = qrcode.make(token)
    buf = BytesIO()
    img.save(buf, format="PNG") # Forzamos formato PNG
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="image/png")