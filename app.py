from flask import Flask, request, jsonify, render_template
from datetime import datetime

app = Flask(__name__)

# Lista en memoria para almacenar los mensajes.
messages = []

# Ruta para la interfaz de App 1 (por ejemplo, una interfaz de estilo claro)
@app.route('/app1')
def app1():
    return render_template('app1.html')

# Ruta para la interfaz de App 2 (por ejemplo, una interfaz de estilo oscuro)
@app.route('/app2')
def app2():
    return render_template('app2.html')

# Endpoint para enviar mensajes (se usa por ambas interfaces)
@app.route('/send', methods=['POST'])
def send_message():
    data = request.get_json()
    
    # Validación básica de los datos recibidos.
    if not data or 'sender' not in data or 'recipient' not in data or 'message' not in data:
        return jsonify({'error': 'Formato inválido. Se requieren: sender, recipient y message.'}), 400

    # Crear el mensaje con un timestamp.
    new_message = {
        'sender': data['sender'],
        'recipient': data['recipient'],
        'message': data['message'],
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    messages.append(new_message)
    
    return jsonify({'status': 'Mensaje enviado!', 'message': new_message}), 200

# Endpoint para obtener mensajes (se usa por ambas interfaces)
@app.route('/messages', methods=['GET'])
def get_messages():
    # Se pueden pasar los parámetros sender y recipient para filtrar.
    sender = request.args.get('sender')
    recipient = request.args.get('recipient')
    
    filtered_messages = messages

    if sender:
        filtered_messages = [msg for msg in filtered_messages if msg['sender'] == sender]
    if recipient:
        filtered_messages = [msg for msg in filtered_messages if msg['recipient'] == recipient]

    return jsonify(filtered_messages), 200

if __name__ == '__main__':
    # Render inyecta la variable de entorno PORT.
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
