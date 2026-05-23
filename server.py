from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from datetime import datetime
import threading
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__)
CORS(app)

# =============================================
# CONFIGURACIÓN DE LA BASE DE DATOS (Clever Cloud)
# =============================================
DB_CONFIG = {
    'host': 'b1itk5vuskow4a4mljf8-mysql.services.clever-cloud.com',
    'user': 'uk2coc2buc33hwlo',
    'password': '3pGDG80KJ0zLm7xDLIcu',
    'database': 'b1itk5vuskow4a4mljf8',
    'port': 3306
}

# =============================================
# CONFIGURACIÓN DE SENDGRID
# =============================================
import os
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
FROM_EMAIL = "sescolarinformes@gmail.com"

# =============================================
# FUNCIÓN PARA ENVIAR CORREO (en hilo separado)
# =============================================
def enviar_correo_sendgrid(nombre, destinatario, tipo_escuela):
    try:
        subject = f'¡Gracias por contactarnos, {nombre}! - SEscolar.ce'

        # Diseño profesional del correo (HTML + texto plano)
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gracias por tu interés | SEscolar.ce</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f7fc;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }}
        .header {{
            background-color: #1E6DF2;
            padding: 20px;
            text-align: center;
        }}
        .header h1 {{
            color: #ffffff;
            margin: 0;
            font-size: 1.8rem;
            letter-spacing: -0.5px;
        }}
        .content {{
            padding: 28px;
            color: #2c3e50;
            line-height: 1.5;
        }}
        .highlight {{
            background-color: #eef3fc;
            border-left: 4px solid #1E6DF2;
            padding: 12px 16px;
            margin: 20px 0;
            border-radius: 6px;
        }}
        .button {{
            display: inline-block;
            background-color: #1E6DF2;
            color: #ffffff;
            text-decoration: none;
            padding: 10px 24px;
            border-radius: 40px;
            margin-top: 16px;
            font-weight: 500;
        }}
        .footer {{
            background-color: #f8fafc;
            padding: 16px;
            text-align: center;
            font-size: 0.8rem;
            color: #6c7e91;
            border-top: 1px solid #eaeef5;
        }}
        .spam-note {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px 15px;
            margin-top: 20px;
            font-size: 0.85rem;
            border-radius: 6px;
            color: #856404;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>SEscolar.ce</h1>
        </div>
        <div class="content">
            <p>Hola <strong>{nombre}</strong>,</p>
            <p>¡Gracias por ponerte en contacto con <strong>SEscolar.ce</strong>!</p>
            <p>Hemos recibido tu solicitud de información para <strong>{tipo_escuela}</strong>.</p>
            <div class="highlight">
                 Tu registro se ha completado exitosamente. En breve, un asesor especializado se comunicará contigo para ofrecerte una demostración personalizada.
            </div>
            <p>Mientras tanto, puedes conocer más sobre nuestras soluciones visitando nuestro sitio web.</p>
            <p style="text-align: center;">
                <a href="https://sescolar.ce" class="button">Conoce SEscolar.ce</a>
            </p>
            <div class="spam-note">
                 <strong>¿No ves este correo en tu bandeja de entrada?</strong> Por favor, revisa tu carpeta de <strong>correo no deseado / spam</strong> y márcalo como "No es spam" para asegurar que recibas nuestros mensajes en el futuro.
            </div>
            <hr style="margin: 24px 0;">
            <p>Saludos cordiales,<br><strong>Equipo SEscolar.ce</strong><br><a href="https://sescolar.ce" style="color: #1E6DF2;">https://sescolar.ce</a></p>
        </div>
        <div class="footer">
            <p>Este es un mensaje automático, por favor no responder.</p>
            <p>&copy; 2025 SEscolar.ce – Soluciones educativas integrales</p>
        </div>
    </div>
</body>
</html>
        """

        # Texto plano alternativo (para clientes de correo que no soporten HTML)
        plain_text = f"""
Hola {nombre},

¡Gracias por contactar a SEscolar.ce! Hemos recibido tu solicitud para {tipo_escuela}.

En breve un asesor se comunicará contigo.

---
 IMPORTANTE: Si no ves este correo en tu bandeja de entrada, revisa tu carpeta de SPAM o correo no deseado. Agréganos a tu lista de contactos para futuras comunicaciones.

Saludos,
Equipo SEscolar.ce
"""

        # Crear el mensaje
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=destinatario,
            subject=subject,
            html_content=html_content,
            plain_text_content=plain_text
        )

        # Enviar con SendGrid
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        if response.status_code == 202:
            print(f"Correo enviado exitosamente a {destinatario}")
        else:
            print(f"Error al enviar correo a {destinatario}: código {response.status_code}")

    except Exception as e:
        print(f"Excepción enviando correo a {destinatario}: {e}")

# =============================================
# RUTA PRINCIPAL
# =============================================
@app.route('/nuevo_lead', methods=['POST'])
def nuevo_lead():
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        correo = data.get('correo')
        tipo_escuela = data.get('tipo_escuela')
        fecha = datetime.now()

        # Guardar en base de datos
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                correo VARCHAR(100) NOT NULL,
                tipo_escuela VARCHAR(50) NOT NULL,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute(
            "INSERT INTO leads (nombre, correo, tipo_escuela, fecha_registro) VALUES (%s, %s, %s, %s)",
            (nombre, correo, tipo_escuela, fecha)
        )
        conn.commit()
        cursor.close()
        conn.close()

        # Enviar correo en segundo plano
        threading.Thread(target=enviar_correo_sendgrid, args=(nombre, correo, tipo_escuela)).start()

        return jsonify({'status': 'ok', 'mensaje': 'Lead guardado, correo en proceso'}), 200

    except Exception as e:
        print('Error:', e)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
