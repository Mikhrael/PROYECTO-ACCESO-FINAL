from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import qrcode
from io import BytesIO
import uuid
from supabase import create_client

# --- CONEXIÓN ---
URL = "https://acvlmncnfayjrjitmspq.supabase.co"
KEY = "TU_ANON_KEY_AQUI" # Asegúrate de que sea tu llave completa
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
    
    # Guardamos con todos los campos de tu tabla
    try:
        supabase.table("accesos").insert({
            "casa": casa, 
            "token": token, 
            "tipo": "Temporal", 
            "usado": False
        }).execute()
    except Exception as e:
        print(f"Error en Supabase: {e}")

    img = qrcode.make(token)
    buf = BytesIO()
    img.save(buf, format="PNG") # Forzamos formato PNG
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="image/png")