import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

#função para enviar o alerta de preço
def enviar_alerta(nome_produto: str, preco_anterior: float, preco_atual: float, url: str):
    #variaveis do .env para enviar o email
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    destino = os.getenv("EMAIL_DESTINO")

    #calcula a porcentagem de queda do preço
    queda_pct = ((preco_anterior - preco_atual) / preco_anterior) * 100

    #assunto do email
    assunto = f"[PriceWatch] Queda de preco: {nome_produto}"

    #corpo do email
    corpo_html = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #e44;">Alerta de Queda de Preco</h2>
        <p><strong>Produto:</strong> {nome_produto}</p>
        <table style="border-collapse: collapse; margin: 16px 0;">
            <tr>
                <td style="padding: 8px 16px; background:#f5f5f5;">Preco anterior</td>
                <td style="padding: 8px 16px;">R$ {preco_anterior:.2f}</td>
            </tr>
            <tr>
                <td style="padding: 8px 16px; background:#f5f5f5;">Preco atual</td>
                <td style="padding: 8px 16px; color: green;"><strong>R$ {preco_atual:.2f}</strong></td>
            </tr>
            <tr>
                <td style="padding: 8px 16px; background:#f5f5f5;">Reducao</td>
                <td style="padding: 8px 16px; color: green;"><strong>{queda_pct:.1f}%</strong></td>
            </tr>
        </table>
        <a href="{url}" style="display:inline-block; padding:12px 24px; background:#e44; color:#fff;
           text-decoration:none; border-radius:4px;">Ver produto</a>
    </body></html>
    """

    #cria o objeto MIMEMultipart
    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = smtp_user
    msg["To"] = destino
    msg.attach(MIMEText(corpo_html, "html"))

    #conecta ao servidor SMTP e envia o email
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, destino, msg.as_string())
