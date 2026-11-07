"""Conexión con el modelo de inteligencia artificial.

Este es el ÚNICO archivo que tienes que completar para conectar la IA.
El resto de la app (la pantalla "Asistente IA") ya arma la pregunta con los
datos del producto y muestra la respuesta.

Pasos:
1. Pon tu clave y modelo en el archivo .env:
       IA_API_KEY=tu-clave
       IA_MODELO=nombre-del-modelo
       IA_API_URL=https://...   (si tu API lo necesita)
2. Completa la función consultar_ia() de abajo.
"""
from flask import current_app
import requests


class IANoConfigurada(Exception):
    """Se lanza mientras la API todavía no está conectada."""


def ia_configurada() -> bool:
    return bool(current_app.config.get("IA_API_KEY"))


def consultar_ia(instrucciones: str, pregunta: str) -> str:
    """Envía la pregunta a la IA y devuelve su respuesta como texto.

    :param instrucciones: el rol de la IA (ej: "Eres asesor de una cafetería...")
    :param pregunta: lo que se le pregunta, ya con los datos del producto
    :return: el texto de la respuesta
    """
    api_key = current_app.config.get("IA_API_KEY")
    modelo = current_app.config.get("IA_MODELO")
    api_url = current_app.config.get("IA_API_URL")

    if not api_key:
        raise IANoConfigurada(
            "La IA todavía no está conectada. Agrega IA_API_KEY en el archivo "
            ".env y completa la función consultar_ia() en app/ia.py."
        )

    respuesta = requests.post(
        api_url or "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": modelo or "openai/gpt-oss-120b",
            "messages": [
                {"role": "system", "content": instrucciones},
                {"role": "user", "content": pregunta},
            ],
            "temperature": 0.5,
        },
        timeout=30,
    )
    if not respuesta.ok:
        # Muestra el motivo que da Groq (ej: modelo no existe, clave inválida)
        try:
            motivo = respuesta.json().get("error", {}).get("message")
        except ValueError:
            motivo = None
        raise RuntimeError(motivo or f"Error {respuesta.status_code} de la API")
    datos = respuesta.json()
    return datos["choices"][0]["message"]["content"]
