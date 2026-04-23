import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

#função para enviar o alerta de preço
def enviar_alerta(nome_produto: str, preco_anterior: float | None, preco_atual: float, url: str, eh_minimo_historico: bool = False):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    destino = os.getenv("EMAIL_DESTINO")

    badge_minimo = '<p style="background:#fff3cd;border:1px solid #ffc107;padding:8px 12px;border-radius:4px;">Menor preco ja registrado para este produto</p>' if eh_minimo_historico else ""

    linha_anterior = f'<tr><td style="padding:8px 16px;background:#f5f5f5;">Preco anterior</td><td style="padding:8px 16px;">R$ {preco_anterior:.2f}</td></tr>' if preco_anterior is not None else ""

    if preco_anterior is not None and preco_anterior > preco_atual:
        queda_pct = ((preco_anterior - preco_atual) / preco_anterior) * 100
        linha_reducao = f'<tr><td style="padding:8px 16px;background:#f5f5f5;">Reducao</td><td style="padding:8px 16px;color:green;"><strong>{queda_pct:.1f}%</strong></td></tr>'
    else:
        linha_reducao = ""

    assunto = f"[PriceWatch] {'Minimo historico: ' if eh_minimo_historico else 'Preco alvo atingido: '}{nome_produto}"

    corpo_html = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #e44;">Alerta de Preco — PriceWatch</h2>
        {badge_minimo}
        <p><strong>Produto:</strong> {nome_produto}</p>
        <table style="border-collapse: collapse; margin: 16px 0;">
            {linha_anterior}
            <tr>
                <td style="padding: 8px 16px; background:#f5f5f5;">Preco atual</td>
                <td style="padding: 8px 16px; color: green;"><strong>R$ {preco_atual:.2f}</strong></td>
            </tr>
            {linha_reducao}
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
