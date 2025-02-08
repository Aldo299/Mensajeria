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

# Conjunto global para almacenar los nombres de usuario registrados.
registered_users = set()

########################################
# Rutas para las interfaces web
########################################

@app.route('/')
def home():
    return render_template('home.html')
    
@app.route('/app1')
def app1():
    return render_template('app1.html')

@app.route('/app2')
def app2():
    return render_template('app2.html')

########################################
# Endpoints para el registro y la gestión de salas y chats
########################################

# Registro de usuario: se verifica que el nombre no se repita (se hace una única vez al escoger el nombre).
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or 'username' not in data:
        return jsonify({'error': 'Se requiere el parámetro username.'}), 400
    username = data['username'].strip()
    if username == "":
        return jsonify({'error': 'El nombre de usuario no puede estar vacío.'}), 400
    if username in registered_users:
        return jsonify({'error': 'El nombre de usuario ya está en uso.'}), 400
    registered_users.add(username)
    return jsonify({'status': 'Usuario registrado', 'username': username}), 200

# Nuevo endpoint para que un administrador se una automáticamente a todas las salas existentes.
@app.route('/admin/join_all', methods=['POST'])
def admin_join_all():
    data = request.get_json()
    if not data or 'admin' not in data:
        return jsonify({'error': 'Se requiere el parámetro admin.'}), 400
    admin = data['admin'].strip()
    # Se asume que el administrador ya está registrado.
    for room in chat_rooms:
        chat_rooms[room]['users'].add(admin)
    return jsonify({'status': f'Administrador {admin} se ha unido a todas las salas.'}), 200

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
    room = data['room'].strip()
    admin = data['admin'].strip()
    # Verificar que no exista una sala con el mismo nombre.
    if room in chat_rooms:
        return jsonify({'error': 'La sala ya existe.'}), 400
    # Se asume que el administrador ya fue registrado.
    chat_rooms[room] = {
        'admin': admin,
        'users': set([admin]),  # Se agrega automáticamente el administrador a la sala.
        'messages': []
    }
    return jsonify({'status': 'Sala creada', 'room': room}), 200

# Unirse a una sala (usado tanto por administradores como por usuarios)
@app.route('/rooms/join', methods=['POST'])
def join_room():
    data = request.get_json()
    if not data or 'room' not in data or 'user' not in data:
        return jsonify({'error': 'Formato inválido. Se requieren: room, user'}), 400
    room = data['room'].strip()
    user = data['user'].strip()
    if room not in chat_rooms:
        return jsonify({'error': 'La sala no existe.'}), 404
    # Se asume que el usuario ya fue registrado.
    if user in chat_rooms[room]['users']:
        return jsonify({'status': f'El usuario {user} ya está en la sala {room}.'}), 200
    chat_rooms[room]['users'].add(user)
    return jsonify({'status': f'Usuario {user} se unió a la sala {room}.'}), 200

# Enviar un mensaje a una sala.
@app.route('/send', methods=['POST'])
def send_message():
    data = request.get_json()
    if not data or 'room' not in data or 'sender' not in data or 'message' not in data:
        return jsonify({'error': 'Formato inválido. Se requieren: room, sender, message.'}), 400
    room = data['room'].strip()
    sender = data['sender'].strip()
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
    room = room.strip()
    if room not in chat_rooms:
        return jsonify({'error': 'La sala no existe.'}), 404
    return jsonify(chat_rooms[room]['messages']), 200

# Remover a un usuario de una sala (solo el administrador puede hacerlo).
@app.route('/rooms/remove_user', methods=['POST'])
def remove_user():
    data = request.get_json()
    if not data or 'room' not in data or 'admin' not in data or 'user' not in data:
        return jsonify({'error': 'Formato inválido. Se requieren: room, admin, user.'}), 400
    room = data['room'].strip()
    admin = data['admin'].strip()
    user = data['user'].strip()
    if room not in chat_rooms:
        return jsonify({'error': 'La sala no existe.'}), 404
    if chat_rooms[room]['admin'] != admin:
        return jsonify({'error': 'Solo el administrador puede remover usuarios.'}), 403
    if user not in chat_rooms[room]['users']:
        return jsonify({'error': 'El usuario no está en la sala.'}), 400
    if user == admin:
        return jsonify({'error': 'El administrador no puede removerse a sí mismo.'}), 400
    chat_rooms[room]['users'].remove(user)
    return jsonify({'status': f'Usuario {user} removido de la sala {room}.'}), 200

########################################
# Configuración de la aplicación
########################################

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
