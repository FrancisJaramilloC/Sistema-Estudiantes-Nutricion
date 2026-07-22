import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app import config

logger = logging.getLogger(__name__)

RESET_EMAIL_SUBJECT = "NutriA — Restablecimiento de Contraseña"

RESET_EMAIL_BODY_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <style>
    body {{ font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }}
    .container {{ max-width: 480px; margin: 0 auto; background: #fff; border-radius: 12px; padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
    h2 {{ color: #1a3c20; margin-bottom: 8px; }}
    .token-box {{ background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 16px; text-align: center; margin: 20px 0; }}
    .token {{ font-size: 1.3rem; font-weight: 700; letter-spacing: 2px; color: #166534; font-family: monospace; word-break: break-all; }}
    .footer {{ font-size: 0.8rem; color: #888; margin-top: 24px; border-top: 1px solid #eee; padding-top: 12px; }}
    p {{ color: #444; font-size: 0.9rem; line-height: 1.5; }}
  </style>
</head>
<body>
  <div class="container">
    <h2>NutriA</h2>
    <p>Hola,</p>
    <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta asociada al correo <strong>{email}</strong>.</p>
    <p>Utiliza el siguiente código de verificación para restablecer tu contraseña:</p>
    <div class="token-box">
      <div class="token">{token}</div>
    </div>
    <p>Este código expira en <strong>1 hora</strong>.</p>
    <p>Si no solicitaste este cambio, puedes ignorar este mensaje de forma segura.</p>
    <div class="footer">
      Este es un correo generado automáticamente por el Sistema NutriA. No respondas a este mensaje.
    </div>
  </div>
</body>
</html>
"""


def is_smtp_configured() -> bool:
    return bool(config.SMTP_HOST and config.SMTP_USER and config.SMTP_FROM)


def send_reset_email(to_email: str, username: str, reset_token: str) -> bool:
    if not is_smtp_configured():
        logger.warning("SMTP no configurado — no se envió correo de restablecimiento.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = RESET_EMAIL_SUBJECT
    msg["From"] = config.SMTP_FROM
    msg["To"] = to_email

    html_body = RESET_EMAIL_BODY_TEMPLATE.format(email=to_email, token=reset_token)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=10) as server:
            server.ehlo()
            if config.SMTP_PORT != 25:
                server.starttls()
                server.ehlo()
            if config.SMTP_USER and config.SMTP_PASS:
                server.login(config.SMTP_USER, config.SMTP_PASS)
            server.sendmail(config.SMTP_FROM, [to_email], msg.as_string())
        logger.info(f"Correo de restablecimiento enviado a {to_email}")
        return True
    except Exception as e:
        logger.error(f"Error al enviar correo de restablecimiento a {to_email}: {e}")
        return False
