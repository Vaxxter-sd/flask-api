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
    # ... (todo el contenido de la función se mantiene igual, no lo cambio)
    # No modifiques esta parte, ya está bien.
    pass  # (yo pondría el código completo aquí, pero por espacio no lo copio)

# =============================================
# RUTA PRINCIPAL CON VERIFICACIÓN DE DUPLICADOS
# =============================================
@app.route('/nuevo_lead', methods=['POST'])
def nuevo_lead():
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        correo = data.get('correo')
        tipo_escuela = data.get('tipo_escuela')
        fecha = datetime.now()

        # Conectar a la base de datos
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Verificar si el correo ya existe (evitar duplicados)
        cursor.execute("SELECT id FROM leads WHERE correo = %s", (correo,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'status': 'error', 'mensaje': 'Este correo ya está registrado.'}), 400

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
