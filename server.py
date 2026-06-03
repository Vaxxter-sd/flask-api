from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from datetime import datetime
import threading
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os

app = Flask(__name__)
CORS(app)

# =============================================
# CONFIGURACION DE LA BASE DE DATOS (Clever Cloud)
# =============================================
DB_CONFIG = {
    'host': 'b1itk5vuskow4a4mljf8-mysql.services.clever-cloud.com',
    'user': 'uk2coc2buc33hwlo',
    'password': '3pGDG80KJ0zLm7xDLIcu',
    'database': 'b1itk5vuskow4a4mljf8',
    'port': 3306
}

# =============================================
# CONFIGURACION DE SENDGRID
# =============================================
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
FROM_EMAIL = "sescolarinformes@gmail.com"
NOTIFY_EMAIL = "carlos213244@gmail.com"   # Correo que recibira la notificacion

# =============================================
# FUNCION PARA ENVIAR CORREO (en hilo separado)
# =============================================
def enviar_correo_sendgrid(nombre, destinatario, tipo_escuela):
    try:
        subject = f'Gracias por contactarnos, {nombre} - SEscolar.ce'
        
        # Enlace a tu landing page (completo con https)
        landing_url = "https://chimerical-twilight-e7b3e1.netlify.app"

        html_content = f"""
        <html>
        <body style="font-family: Arial; background:#f4f7fc; padding:20px;">
            <div style="max-width:600px; margin:auto; background:#fff; border-radius:16px; padding:20px;">
                <h1 style="color:#1E6DF2;">SEscolar.ce</h1>
                <p>Hola <strong>{nombre}</strong>,</p>
                <p>Gracias por tu interes. Hemos recibido tu solicitud para <strong>{tipo_escuela}</strong>.</p>
                <p>Un asesor se comunicara contigo en breve.</p>
                <div style="text-align:center; margin: 30px 0;">
                    <a href="{landing_url}" style="background-color:#1E6DF2; color:#ffffff; padding:12px 24px; text-decoration:none; border-radius:40px; font-weight:bold;">Visitar nuestro sitio</a>
                </div>
                <hr>
                <p style="font-size:12px; color:gray;">Si no ves este correo en tu bandeja de entrada, revisa tu carpeta de spam.</p>
            </div>
        </body>
        </html>
        """
        plain_text = f"""Hola {nombre},

Gracias por contactarnos. Hemos recibido tu solicitud para {tipo_escuela}.

Puedes visitar nuestro sitio web en: {landing_url}

Si no ves este correo en tu bandeja de entrada, revisa tu carpeta de spam.

Saludos,
Equipo SEscolar.ce"""

        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=destinatario,
            subject=subject,
            html_content=html_content,
            plain_text_content=plain_text
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        if response.status_code == 202:
            print(f"Correo enviado exitosamente a {destinatario}")
        else:
            print(f"Error al enviar correo a {destinatario}: codigo {response.status_code}")

        # =============================================
        # Enviar notificacion al administrador
        # =============================================
        subject_admin = f'Nuevo lead registrado: {nombre}'
        html_admin = f"""
        <html>
        <body>
            <h2>Nuevo lead en SEscolar.ce</h2>
            <p><strong>Nombre:</strong> {nombre}</p>
            <p><strong>Correo:</strong> {destinatario}</p>
            <p><strong>Tipo de escuela:</strong> {tipo_escuela}</p>
            <p><strong>Fecha:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <hr>
            <p>Este es un aviso automatico del sistema de captacion de leads.</p>
        </body>
        </html>
        """
        message_admin = Mail(
            from_email=FROM_EMAIL,
            to_emails=NOTIFY_EMAIL,
            subject=subject_admin,
            html_content=html_admin
        )
        sg.send(message_admin)
        print(f"Notificacion enviada a {NOTIFY_EMAIL}")

    except Exception as e:
        print(f"Excepcion enviando correos: {e}")

# =============================================
# RUTA PRINCIPAL CON VERIFICACION DE DUPLICADOS
# =============================================
@app.route('/nuevo_lead', methods=['POST'])
def nuevo_lead():
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        correo = data.get('correo')
        tipo_escuela = data.get('tipo_escuela')
        fecha = datetime.now()

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Verificar si el correo ya existe (evitar duplicados)
        cursor.execute("SELECT id FROM leads WHERE correo = %s", (correo,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'status': 'error', 'mensaje': 'Este correo ya esta registrado.'}), 400

        # Insertar nuevo lead (la tabla ya existe, no la volvemos a crear)
        sql = "INSERT INTO leads (nombre, correo, tipo_escuela, fecha_registro) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (nombre, correo, tipo_escuela, fecha))
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
