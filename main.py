import os
import requests
from fastapi import FastAPI, Request, Response

app = FastAPI()

# Estas llaves las configurarás en tu plataforma de alojamiento (ej. Vercel)
TOKEN_VERIFICACION = os.getenv("TOKEN_VERIFICACION") # Tú inventas una contraseña
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")         # Te lo da Meta
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")         # Te lo da OpenAI

# 1. RUTA DE VERIFICACIÓN (Meta te exige esto para conectar tu número)
@app.get("/webhook")
async def verificar_whatsapp(request: Request):
    # Meta enviará estos datos para comprobar que el webhook es tuyo
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == TOKEN_VERIFICACION:
        return Response(content=challenge, media_type="text/plain")
    return {"error": "Token de verificación inválido"}

# 2. RUTA PARA RECIBIR MENSAJES
@app.post("/webhook")
async def recibir_mensaje(request: Request):
    datos = await request.json()

    # Verificamos que el mensaje venga de un usuario real de WhatsApp
    try:
        mensaje_info = datos["entry"][0]["changes"][0]["value"]["messages"][0]
        numero_cliente = mensaje_info["from"]
        texto_cliente = mensaje_info["text"]["body"]
        
        # 3. Enviamos lo que dijo el cliente a la IA (ChatGPT)
        respuesta_ia = consultar_chatgpt(texto_cliente)
        
        # 4. Devolvemos la respuesta inteligente al WhatsApp del cliente
        enviar_whatsapp(numero_cliente, respuesta_ia)
        
    except KeyError:
        # Si llega algo que no es un mensaje (ej. una confirmación de lectura), lo ignoramos
        pass

    return {"status": "ok"}

# --- FUNCIONES AUXILIARES ---

def consultar_chatgpt(texto):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "Eres un asistente de ventas amable para un local en Panamá. Responde corto y al grano."},
            {"role": "user", "content": texto}
        ]
    }
    respuesta = requests.post(url, headers=headers, json=data)
    return respuesta.json()["choices"][0]["message"]["content"]

def enviar_whatsapp(numero, texto):
    # Esta es la URL oficial de Meta para enviar mensajes
    url = "https://graph.facebook.com/v17.0/TU_NUMERO_DE_TELEFONO_ID/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }
    requests.post(url, headers=headers, json=data)
