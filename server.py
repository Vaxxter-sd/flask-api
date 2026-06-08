from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from datetime import datetime
import threading
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
import requests

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
NOTIFY_EMAIL = "jolopezhu1458@uaemex.mx"   # Solo este recibirá correo

# =============================================
# CONFIGURACION DEL CRM (Django) - Endpoint
# =============================================
CRM_API_URL = "https://django-railway-production-c6f7.up.railway.app/api/recibir-lead/"

# =============================================
# FUNCION PARA ENVIAR CORREO (solo al administrador)
# =============================================
def enviar_correo_admin(nombre, destinatario, tipo_escuela):
    try:
        # =============================================
        # NOTIFICACIÓN AL ADMINISTRADOR (se mantiene)
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
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message_admin)
        print(f"Notificacion enviada a {NOTIFY_EMAIL}")

    except Exception as e:
        print(f"Excepcion enviando correo al administrador: {e}")

# =============================================
# FUNCION PARA ENVIAR LEAD AL CRM VIA API
# =============================================
def enviar_lead_a_crm(nombre, correo, tipo_escuela, fecha_registro):
    try:
        payload = {
            "nombre": nombre,
            "correo": correo,
            "tipo_escuela": tipo_escuela,
            "fecha_registro": fecha_registro.isoformat()
        }
        response = requests.post(CRM_API_URL, json=payload, timeout=5)
        if response.status_code in (200, 201):
            print(f"Lead enviado al CRM exitosamente para {correo}")
        else:
            print(f"Error al enviar lead al CRM: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Excepción al enviar lead al CRM: {e}")

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

        # Enviar notificación al administrador en segundo plano (sin correo al lead)
        threading.Thread(target=enviar_correo_admin, args=(nombre, correo, tipo_escuela)).start()

        # Enviar lead al CRM en segundo plano
        threading.Thread(target=enviar_lead_a_crm, args=(nombre, correo, tipo_escuela, fecha)).start()

        return jsonify({'status': 'ok', 'mensaje': 'Lead guardado, notificacion enviada'}), 200

    except Exception as e:
        print('Error:', e)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
