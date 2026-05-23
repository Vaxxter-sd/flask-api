from flask import Flask, request, jsonify
from flask_cors import CORS 
import mysql.connector
import smtplib
from email.message import EmailMessage
from datetime import datetime

app = Flask(__name__)
CORS(app)

# =============================================
# CONFIGURACIÓN DE LA BASE DE DATOS
# =============================================
# Configuración de la base de datos (lee variables de entorno de Railway)
DB_CONFIG = {
    'host': 'kodama.proxy.rlwy.net',
    'user': 'root',
    'password': 'uAWtpgQEHbDcTFiJOmxratreEnpIJXjb',  # tu contraseña completa
    'database': 'railway',
    'port': 38086   # ← importante, no es 3306
}

# =============================================
# CONFIGURACIÓN DEL CORREO ELECTRÓNICO
# =============================================
SMTP_CONFIG = {
    'server': 'smtp.gmail.com',
    'port': 587,
    'user': 'sescolarinformes@gmail.com',
    'password': 'buwu imql jbol brae'
}

# =============================================
# RUTA PRINCIPAL: Recibe los datos del formulario
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
        sql = "INSERT INTO leads (nombre, correo, tipo_escuela, fecha_registro) VALUES (%s, %s, %s, %s)"
        valores = (nombre, correo, tipo_escuela, fecha)
        cursor.execute(sql, valores)
        conn.commit()
        cursor.close()
        conn.close()

        # Enviar correo de confirmación con diseño HTML
        msg = EmailMessage()
        msg['Subject'] = f'¡Gracias por contactarnos, {nombre}! - SEscolar.ce'
        msg['From'] = SMTP_CONFIG['user']
        msg['To'] = correo

        # Texto plano (alternativo)
        texto_plano = f"""Hola {nombre},

Gracias por tu interés en SEscolar.ce.

Hemos recibido tu solicitud de información para {tipo_escuela}. En breve, un asesor se comunicará contigo para brindarte una demostración personalizada.

Saludos cordiales,
Equipo SEscolar.ce
"""

        # HTML personalizado
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gracias por contactarnos</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background-color: #f4f7fc;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }}
        .header {{
            background-color: #1E6DF2;
            padding: 24px;
            text-align: center;
        }}
        .header h1 {{
            color: #ffffff;
            margin: 0;
            font-size: 1.8rem;
            letter-spacing: -0.5px;
        }}
        .content {{
            padding: 32px;
        }}
        .content p {{
            color: #2c3e50;
            line-height: 1.5;
            margin-bottom: 16px;
        }}
        .highlight {{
            background-color: #eef3fc;
            border-left: 4px solid #1E6DF2;
            padding: 12px 16px;
            margin: 20px 0;
            border-radius: 8px;
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
            padding: 20px;
            text-align: center;
            color: #6c7e91;
            font-size: 0.8rem;
            border-top: 1px solid #eaeef5;
        }}
        .footer a {{
            color: #1E6DF2;
            text-decoration: none;
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
            <p>¡Gracias por ponerte en contacto con <strong>SEscolar.ce</strong>! Hemos recibido tu solicitud de información para <strong>{tipo_escuela}</strong>.</p>
            <div class="highlight">
                 Tu registro se ha completado exitosamente.
            </div>
            <p>Un asesor especializado se comunicará contigo en las próximas horas para ofrecerte una demostración personalizada y resolver todas tus dudas sobre nuestra plataforma de gestión educativa.</p>
            <p>Mientras tanto, puedes conocer más sobre nuestras soluciones visitando nuestro sitio web.</p>
            <p style="text-align: center;">
                <a href="https://sescolar.ce" class="button">Conoce SEscolar.ce</a>
            </p>
            <hr style="margin: 24px 0; border: 0; border-top: 1px solid #eaeef5;">
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

        msg.set_content(texto_plano)
        msg.add_alternative(html, subtype='html')

        with smtplib.SMTP(SMTP_CONFIG['server'], SMTP_CONFIG['port']) as smtp:
            smtp.starttls()
            smtp.login(SMTP_CONFIG['user'], SMTP_CONFIG['password'])
            smtp.send_message(msg)

        return jsonify({'status': 'ok', 'mensaje': 'Lead guardado y correo enviado'}), 200

    except Exception as e:
        print('Error:', e)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)