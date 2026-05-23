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
FROM_EMAIL = "sescolarinformes@gmail.com"   # Remitente verificado

# =============================================
# FUNCIÓN PARA ENVIAR CORREO (en hilo separado)
# =============================================
def enviar_correo_sendgrid(nombre, destinatario, tipo_escuela):
    try:
        subject = f'¡Gracias por contactarnos, {nombre}! - SEscolar.ce'
        html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Gracias</title></head>
<body style="font-family: Arial; background:#f4f7fc; padding:20px;">
    <div style="max-width:600px; margin:auto; background:#fff; border-radius:16px; padding:20px;">
        <h1 style="color:#1E6DF2;">SEscolar.ce</h1>
        <p>Hola <strong>{nombre}</strong>,</p>
        <p>¡Gracias por tu interés! Hemos recibido tu solicitud para <strong>{tipo_escuela}</strong>.</p>
        <p>Un asesor se comunicará contigo en breve.</p>
        <hr>
        <p style="font-size:12px; color:gray;">Este es un mensaje automático.</p>
    </div>
</body>
</html>
"""
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=destinatario,
            subject=subject,
            html_content=html
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        if response.status_code == 202:
            print(f"Correo enviado a {destinatario}")
        else:
            print(f"Error al enviar: {response.status_code}")
    except Exception as e:
        print(f"Excepción en envío de correo: {e}")

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

        # Enviar correo sin bloquear la respuesta
        threading.Thread(target=enviar_correo_sendgrid, args=(nombre, correo, tipo_escuela)).start()

        return jsonify({'status': 'ok', 'mensaje': 'Lead guardado, correo en proceso'}), 200

    except Exception as e:
        print('Error:', e)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
