from email.mime.multipart import MIMEMultipart
import requests
import os
from email.utils import make_msgid
from email.mime.image import MIMEImage
from uuid import UUID

TOKEN = os.getenv("API_KEY")
if not TOKEN:
    raise ValueError("TOKEN environment variable is not set")

def gerar_logo_html(logo: str, msg: MIMEMultipart) -> str:
    if not logo:
        return ""

    try:
        # Baixa a imagem
        if logo.startswith(("http://", "https://")):
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(logo, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"[AVISO] Falha ao baixar logo (status {response.status_code})")
                return ""
            logo_data = response.content
        elif os.path.exists(logo):
            with open(logo, "rb") as f:
                logo_data = f.read()
        else:
            print(f"[AVISO] Logo não encontrada: {logo}")
            return ""

        # Gera um Content-ID único
        image_cid = make_msgid(domain="menezesdigital.com.br")[1:-1]

        # Cria o anexo inline
        img = MIMEImage(logo_data)
        img.add_header("Content-ID", f"<{image_cid}>")
        img.add_header("Content-Disposition", "inline", filename="logo.png")
        msg.attach(img)

        # Retorna HTML para exibir inline
        return f'''
        <div style="text-align:center; margin-bottom:30px;">
            <img src="cid:{image_cid}" alt="Logo" style="width:120px; height:auto;"/>
        </div>
        '''

    except Exception as e:
        print(f"[ERRO] Falha ao gerar logo inline: {e}")
        return ""



def envia_email(email: str, from_address: str, to_address: str, subject: str, password: str, parameters: str, logo: str = None, email_id: UUID = None):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from datetime import datetime

    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        msg = MIMEMultipart("alternative")
        msg["From"] = from_address
        msg["To"] = to_address
        msg["Subject"] = subject

        current_year = datetime.now().year

        logo_html = gerar_logo_html(logo, msg)
        
        footer_html = f"""
        <footer style="margin-top:40px; text-align:center; font-size:13px; color:#999; border-top:1px solid #eee; padding-top:15px;">
            Esta é uma mensagem automática — não responda a este e-mail.<br/>
            &copy; {current_year} · 
            <a href="https://menezesdigital.com.br/" target="_blank" style="color:#999; text-decoration:none;">
                menezesdigital.com.br
            </a>
            <img src="https://apimensageria.menezesdigital.com.br/v2/update-status/{email_id}?Status=visualized&Token={TOKEN}" width="1" height="1" style="display:none;"  />
        </footer>
        """

        if parameters == "error":
            html_content = f"""
            <html>
                <body style="margin:0;padding:0;background:#fdecea;font-family:Arial,sans-serif;"> 
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                        style="background:#fdecea;padding:40px 0;">
                        <tr>
                            <td align="center">
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                                    style="max-width:520px;background:#ffffff;border-radius:10px;box-shadow:0 2px 6px rgba(0,0,0,0.05);">
                                    <tr>
                                        <td style="padding:30px 25px 35px;text-align:center;">  
                                            {logo_html}
                                            <h2 style="color:#b71c1c;margin:18px 0 10px;font-size:20px;">
                                                ⚠️ Erro Detectado
                                            </h2>
                                            <p style="color:#333;font-size:14px;line-height:1.5;margin:0;">
                                                {email}
                                            </p>
                                            <!--<p style="margin-top:18px;color:#555;">
                                                Verifique o sistema o quanto antes.
                                            </p> -->
                                            <div style="margin-top:25px;">
                                                {footer_html}
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </body>
                </html>
            """

        elif parameters == "email":
            html_content = f"""
                <html>
                <body style="margin:0;padding:0;background:#f3f4f6;font-family:Arial,sans-serif;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                        style="background:#f3f4f6;padding:40px 0;">
                        <tr>
                            <td align="center">
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                                    style="max-width:520px;background:#ffffff;border-radius:10px;box-shadow:0 2px 6px rgba(0,0,0,0.05);">             
                                    <tr>
                                        <td style="padding:30px 25px 35px;text-align:center;">                                         
                                            {logo_html}
                                            <h2 style="color:#2563eb;margin:18px 0 10px;font-size:20px;">
                                                📩 Nova Mensagem
                                            </h2>
                                            <p style="color:#333;font-size:14px;line-height:1.5;margin:0;">
                                                {email}
                                            </p>
                                            <div style="margin-top:25px;">
                                                {footer_html}
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </body>
                </html>
            """

        elif parameters == "success":
            html_content = f"""
            <html>
            <body style="margin:0;padding:0;background:#e8f5e9;font-family:Arial,sans-serif;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" 
                    style="background:#e8f5e9;padding:40px 0;">
                    <tr>
                        <td align="center">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                                style="max-width:520px;background:#ffffff;border-radius:10px;box-shadow:0 2px 6px rgba(0,0,0,0.05);">
                                <tr>
                                    <td style="padding:30px 25px 35px;text-align:center;">                                      
                                        {logo_html}
                                        <h2 style="color:#2e7d32;margin:18px 0 10px;font-size:20px;">
                                            ✅ Operação Realizada com Sucesso
                                        </h2>
                                        <p style="color:#333;font-size:14px;line-height:1.5;margin:0;">
                                            {email}
                                        </p>
                                        <div style="margin-top:25px;">
                                            {footer_html}
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """

        elif parameters == "alert":
            html_content = f"""
            <html>
                <body style="margin:0;padding:0;background:#fff8e1;font-family:Arial,sans-serif;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                        style="background:#fff8e1;padding:40px 0;">
                        <tr>
                            <td align="center">
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                                    style="max-width:520px;background:#ffffff;border-radius:10px;box-shadow:0 2px 6px rgba(0,0,0,0.05);">                                   
                                    <tr>
                                        <td style="padding:30px 25px 35px;text-align:center;">                                           
                                            {logo_html}
                                            <h2 style="color:#f57c00;margin:18px 0 10px;font-size:20px;">
                                                ⚠️ Alerta do Sistema
                                            </h2>
                                            <p style="color:#333;font-size:14px;line-height:1.5;margin:0;">
                                                {email}
                                            </p>
                                            <div style="margin-top:25px;">
                                                {footer_html}
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </body>
                </html>
            """

        elif parameters == "welcome":
            html_content = f"""
                <html>
                <body style="margin:0;padding:0;background:#e3f2fd;font-family:Arial,sans-serif;"> 
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                        style="background:#e3f2fd;padding:40px 0;">
                        <tr>
                            <td align="center">
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                                    style="max-width:520px;background:#ffffff;border-radius:10px;box-shadow:0 2px 6px rgba(0,0,0,0.05);">                        
                                    <tr>
                                        <td style="padding:30px 25px 35px;text-align:center;">                                 
                                            {logo_html}
                                            <h2 style="color:#1976d2;margin:18px 0 10px;font-size:20px;">
                                                🎉 Bem-vindo(a)!
                                            </h2>
                                            <p style="color:#333;font-size:14px;line-height:1.5;margin:0;">
                                                {email}
                                            </p>
                                            <p style="margin-top:18px;color:#555;">
                                                Estamos felizes em tê-lo(a) conosco!
                                            </p>
                                            <div style="margin-top:25px;">
                                                {footer_html}
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </body>
                </html>
            """
        
        elif parameters == "sette":
            html_content = f"""
                <!DOCTYPE html>
                <html lang="pt-br">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                </head>
                <body style="margin:0;padding:0;background-color:#dbd7cd;font-family:Arial,sans-serif;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#dbd7cd;padding:40px 10px;">
                        <tr>
                            <td align="center">
                                <!-- Card Principal -->
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:520px;background-color:#f7f6f2;border-radius:10px;box-shadow:0 4px 10px rgba(0,0,0,0.1);overflow:hidden;">
                                    
                                    <!-- Cabeçalho -->
                                    <tr>
                                        <td align="center" style="background-color:#9e5e31;padding:30px 0;">
                                            <img src="https://imobiliaria.menezesdigital.com.br/logo-sette.png" alt="Sette Logo" width="130" style="display:block;border:0;outline:none;text-decoration:none;">
                                        </td>
                                    </tr>

                                    <!-- Conteúdo -->
                                    <tr>
                                        <td style="padding:40px 30px;text-align:left;">
                                            <h2 style="color:#9e5e31;font-size:24px;margin:0 0 20px 0;font-weight:bold;font-family:Arial,sans-serif;">Redefinição de senha</h2>
                                            
                                            <p style="color:#333333;font-size:15px;line-height:1.6;margin:0 0 15px 0;font-family:Arial,sans-serif;">
                                                Recebemos uma solicitação para redefinição de senha da sua conta.
                                            </p>
                                            <p style="color:#333333;font-size:15px;line-height:1.6;margin:0 0 25px 0;font-family:Arial,sans-serif;">
                                                Para redefinir a sua senha de acesso, clique no botão abaixo:
                                            </p>

                                            <!-- Botão (Estilo Bulletproof para E-mail) -->
                                            <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                                                <tr>
                                                    <td align="center" bgcolor="#9e5e31" style="border-radius:6px;">
                                                        {email}
                                                    </td>
                                                </tr>
                                            </table>

                                            <div style="margin-top:35px;border-top:1px solid #dbd7cd;padding-top:25px;">
                                                <p style="color:#666666;font-size:13px;line-height:1.5;margin:0 0 10px 0;font-family:Arial,sans-serif;">
                                                    Se você não reconhece esta solicitação, basta ignorar este e-mail.
                                                </p>
                                                <p style="color:#888888;font-size:12px;margin:0;font-family:Arial,sans-serif;">
                                                    Dúvidas? Entre em contato com o suporte.
                                                </p>
                                            </div>
                                        </td>
                                    </tr>
                                </table>

                                <!-- Rodapé -->
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:520px;margin-top:20px;">
                                    <tr>
                                        <td align="center" style="color:#666666;font-size:12px;font-family:Arial,sans-serif;">
                                            { footer_html }
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </body>
                </html>
            """

        else:
            html_content = f"""
                <html>
                <body style="margin:0;padding:0;background:#f3f4f6;font-family:Arial,sans-serif;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                        style="background:#f3f4f6;padding:40px 0;">
                        <tr>
                            <td align="center">
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                                    style="max-width:520px;background:#ffffff;border-radius:10px;box-shadow:0 2px 6px rgba(0,0,0,0.05);">    
                                    <tr>
                                        <td style="padding:30px 25px 35px;text-align:center;">                                       
                                            {logo_html}
                                            <h2 style="color:#333;margin:18px 0 10px;font-size:20px;">
                                                📢 Notificação
                                            </h2>
                                            <p style="color:#333;font-size:14px;line-height:1.5;margin:0;">
                                                {email}
                                            </p>
                                            <div style="margin-top:25px;">
                                                {footer_html}
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </body>
                </html>
            """


        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_address, password)
            server.send_message(msg)

        print("Mensagem enviada com sucesso!")

    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")
