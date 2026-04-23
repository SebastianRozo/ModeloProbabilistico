import os
import random

import resend

def send_verification_code(email: str) -> str:
    api_key = os.getenv("RESEND_API_KEY") or os.getenv("RESEND_API")
    from_email = os.getenv("RESEND_FROM_EMAIL") or os.getenv("from_email")

    if not api_key:
        raise ValueError("RESEND_API_KEY no esta configurado")

    code = str(random.randint(100000, 999999))
    resend.api_key = api_key

    message = {
        "to": [email],
        "subject": "Codigo de verificacion",
        "html": (
            "<div style='margin:0; padding:0; background-color:#f4f8fb; font-family:Arial, sans-serif;'>"
                "<div style='max-width:600px; margin:40px auto; background:#ffffff; border-radius:16px; "
                "overflow:hidden; box-shadow:0 6px 18px rgba(0,0,0,0.08);'>"

                    "<div style='background:linear-gradient(135deg, #6c63ff, #8ec5fc); padding:30px; text-align:center; color:white;'>"
                        "<h1 style='margin:0; font-size:28px;'>Tu espacio seguro</h1>"
                        "<p style='margin:10px 0 0; font-size:16px;'>Verificación de acceso</p>"
                    "</div>"

                    "<div style='padding:35px; color:#333;'>"
                        "<h2 style='margin-top:0; font-size:22px; color:#2c3e50;'>Hola 👋</h2>"
                        "<p style='font-size:16px; line-height:1.6; color:#555;'>"
                            "Estamos encantados de acompañarte en este proceso. "
                            "Para continuar con tu acceso a la plataforma, utiliza el siguiente código de verificación:"
                        "</p>"

                        "<div style='margin:30px 0; text-align:center;'>"
                            f"<span style='display:inline-block; background:#f3f6ff; color:#6c63ff; "
                            "font-size:32px; font-weight:bold; letter-spacing:6px; padding:18px 30px; "
                            "border-radius:12px; border:2px dashed #cfd8ff;'>"
                                f"{code}"
                            "</span>"
                        "</div>"

                        "<p style='font-size:15px; line-height:1.6; color:#666;'>"
                            "Este código vence en <strong>10 minutos</strong>. "
                            "Si no solicitaste este acceso, puedes ignorar este mensaje."
                        "</p>"

                        "<div style='margin-top:30px; padding:18px; background:#f9fbfd; border-left:4px solid #8ec5fc; border-radius:8px;'>"
                            "<p style='margin:0; font-size:14px; color:#555;'>"
                                "Recuerda: cuidar tu bienestar emocional también es una prioridad 💙"
                            "</p>"
                        "</div>"
                    "</div>"

                    "<div style='background:#f4f8fb; padding:20px; text-align:center; font-size:13px; color:#888;'>"
                        "Este es un mensaje automático de verificación. Por favor, no respondas a este correo."
                    "</div>"

                "</div>"
            "</div>"
        ),
        "text": f"Tu código de verificación es: {code}. Este código vence en 10 minutos.",
    }

    sender = from_email

    try:
        resend.Emails.send({**message, "from": sender})
    except Exception as exc:
            raise

    return code
