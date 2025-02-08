from flask import Flask, request, jsonify, render_template, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# Diccionario para almacenar las salas de chat.
# Estructura: 
# {
#   "nombre_sala": {
#       "admin": "nombre_admin",
#       "users": set([...]),
#       "messages": [ { "room": ..., "sender": ..., "message": ..., "timestamp": ... }, ... ]
#   },
#   ...
# }
chat_rooms = {}

# Conjunto global para almacenar los nombres de usuario activos.
active_users = set()

########################################
# Rutas para las interfaces web
########################################

# Página de inicio (menú)
@app.route('/')
def home():
    return render_template('home.html')
    
# Interfaz para App1 (administrador)
@app.route('/app1')
def app1():
    return render_template('app1.html')

# Interfaz para App2 (usuario común)
@app.route('/app2')
def app2():
    return render_template('app2.html')

########################################
# Endpoints para la gestión de salas y chats
########################################

# Listar todas las salas disponibles.
@app.route('/rooms', methods=['GET'])
def list_rooms():
    rooms_list = []
    for room, data in chat_rooms.items():
        rooms_list.append({
            'room': room,
            'admin': data['admin'],
            'user_count': len(data['users'])
        })
    return jsonify(rooms_list), 200

# Crear una sala (solo la usa el administrador)
@app.route('/rooms', methods=['POST'])
def create_room():
    data = request.get_json()
    if not data or 'room' not in data or 'admin' not in data:
        return jsonify({'error': 'Formato inválido. Se requieren: room, admin'}), 400
    room = data['room']
    admin = data['admin']
    if room in chat_rooms:
        return jsonify({'error': 'La sala ya existe.'}), 400
    # Verificar que el nombre del administrador no esté ya en uso
    if admin in active_users:
        return jsonify({'error': 'El nombre de usuario ya está en uso.'}), 400
    # Agregar el nombre del administrador a los usuarios activos y crear la sala
    active_users.add(admin)
    chat_rooms[room] = {
        'admin': admin,
        'users': set([admin]),  # El admin se agrega automáticamente
        'messages': []
    }
    return jsonify({'status': 'Sala creada', 'room': room}), 200

# Unirse a una sala (usado tanto por admin como por usuarios)
@app.route('/rooms/join', methods=['POST'])
def join_room():
    data = request.get_json()
    if not data or 'room' not in data or 'user' not in data:
        return jsonify({'error': 'Formato inválido. Se requieren: room, user'}), 400
    room = data['room']
    user = data['user']
    if room not in chat_rooms:
        return jsonify({'error': 'La sala no existe.'}), 404
    # Si el usuario ya está en la sala, se informa
    if user in chat_rooms[room]['users']:
        return jsonify({'status': f'El usuario {user} ya está en la sala {room}.'}), 200
    # Si el usuario ya está activo en otra sala, se rechaza la solicitud
    if user in active_users:
        return jsonify({'error': 'El nombre de usuario ya está en uso.'}), 400
    # Agregar el usuario a la sala y al conjunto global
    active_users.add(user)
    chat_rooms[room]['users'].add(user)
    return jsonify({'status': f'Usuario {user} se unió a la sala {room}.'}), 200

# Enviar un mensaje a una sala.
@app.route('/send', methods=['POST'])
def send_message():
    data = request.get_json()
    if not data or 'room' not in data or 'sender' not in data or 'message' not in data:
        return jsonify({'error': 'Formato inválido. Se requieren: room, sender, message.'}), 400
    room = data['room']
    sender = data['sender']
    message_text = data['message']
    if room not in chat_rooms:
        return jsonify({'error': 'La sala no existe.'}), 404
    # Verificar que el usuario se haya unido a la sala.
    if sender not in chat_rooms[room]['users']:
        return jsonify({'error': 'El usuario no se ha unido a esta sala.'}), 403
    new_message = {
        'room': room,
        'sender': sender,
        'message': message_text,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    chat_rooms[room]['messages'].append(new_message)
    return jsonify({'status': 'Mensaje enviado!', 'message': new_message}), 200

# Obtener los mensajes de una sala.
@app.route('/messages', methods=['GET'])
def get_messages():
    room = request.args.get('room')
    if not room:
        return jsonify({'error': 'Se requiere el parámetro room.'}), 400
    if room not in chat_rooms:
        return jsonify({'error': 'La sala no existe.'}), 404
    return jsonify(chat_rooms[room]['messages']), 200

# Remover a un usuario de una sala (solo el administrador puede hacerlo).
@app.route('/rooms/remove_user', methods=['POST'])
def remove_user():
    data = request.get_json()
    if not data or 'room' not in data or 'admin' not in data or 'user' not in data:
        return jsonify({'error': 'Formato inválido. Se requieren: room, admin, user.'}), 400
    room = data['room']
    admin = data['admin']
    user = data['user']
    if room not in chat_rooms:
        return jsonify({'error': 'La sala no existe.'}), 404
    if chat_rooms[room]['admin'] != admin:
        return jsonify({'error': 'Solo el administrador puede remover usuarios.'}), 403
    if user not in chat_rooms[room]['users']:
        return jsonify({'error': 'El usuario no está en la sala.'}), 400
    if user == admin:
        return jsonify({'error': 'El administrador no puede removerse a sí mismo.'}), 400
    chat_rooms[room]['users'].remove(user)
    # Dado que se permite que un usuario esté en una sola sala, lo removemos del conjunto global
    active_users.discard(user)
    return jsonify({'status': f'Usuario {user} removido de la sala {room}.'}), 200

########################################
# Configuración de la aplicación
########################################

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
