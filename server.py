from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import smtplib
from email.message import EmailMessage
from datetime import datetime
import threading   # ← NUEVO: para enviar correo sin bloquear

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
# CONFIGURACIÓN DEL CORREO ELECTRÓNICO (Gmail)
# =============================================
SMTP_CONFIG = {
    'server': 'smtp.gmail.com',
    'port': 587,
    'user': 'sescolarinformes@gmail.com',
    'password': 'buwu imql jbol brae'
}

# =============================================
# FUNCIÓN PARA ENVIAR CORREO EN SEGUNDO PLANO
# =============================================
def enviar_correo_async(nombre, correo, tipo_escuela):
    """
    Envía el correo de confirmación. Esta función se ejecuta en un hilo separado
    para no retrasar la respuesta de la API.
    """
    try:
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

        # HTML personalizado (versión más ligera para mejorar velocidad)
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
        }}
        .content {{
            padding: 32px;
        }}
        .button {{
            display: inline-block;
            background-color: #1E6DF2;
            color: #ffffff;
            text-decoration: none;
            padding: 10px 24px;
            border-radius: 40px;
            margin-top: 16px;
        }}
        .footer {{
            padding: 20px;
            text-align: center;
            color: #6c7e91;
            font-size: 0.8rem;
            border-top: 1px solid #eaeef5;
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
            <p>Un asesor especializado se comunicará contigo en las próximas horas para ofrecerte una demostración personalizada.</p>
            <p style="text-align: center;">
                <a href="https://sescolar.ce" class="button">Conoce SEscolar.ce</a>
            </p>
            <hr style="margin: 24px 0;">
            <p>Saludos cordiales,<br><strong>Equipo SEscolar.ce</strong></p>
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
        print(f"Correo enviado exitosamente a {correo}")
    except Exception as e:
        print(f"Error al enviar correo a {correo}: {e}")

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

        # 1. Guardar en base de datos (rápido)
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        # Crear tabla si no existe (por si acaso)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                correo VARCHAR(100) NOT NULL,
                tipo_escuela VARCHAR(50) NOT NULL,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        sql = "INSERT INTO leads (nombre, correo, tipo_escuela, fecha_registro) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (nombre, correo, tipo_escuela, fecha))
        conn.commit()
        cursor.close()
        conn.close()

        # 2. Enviar correo en segundo plano (sin bloquear la respuesta)
        hilo = threading.Thread(target=enviar_correo_async, args=(nombre, correo, tipo_escuela))
        hilo.start()

        # 3. Responder inmediatamente al usuario
        return jsonify({'status': 'ok', 'mensaje': 'Lead guardado, correo en proceso'}), 200

    except Exception as e:
        print('Error:', e)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500

# =============================================
# PUNTO DE ENTRADA (ejecuta el servidor)
# =============================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
