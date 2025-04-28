from flask import Flask, render_template
from flask_socketio import SocketIO, join_room, leave_room, emit
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_secreto_aqui'
socketio = SocketIO(app, cors_allowed_origins="*")

# Estructura de datos igual que antes
chat_rooms = {}
registered_users = set()

########################################
# Rutas para servir tus páginas
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
# Eventos WebSocket
########################################

@socketio.on('register')
def handle_register(data):
    username = data.get('username', '').strip()
    if not username:
        emit('register_error', {'error': 'Se requiere username.'})
        return
    if username in registered_users:
        emit('register_error', {'error': 'Usuario ya existe.'})
        return
    registered_users.add(username)
    emit('register_success', {'username': username})


@socketio.on('create_room')
def handle_create_room(data):
    room = data.get('room', '').strip()
    admin = data.get('admin', '').strip()
    if not room or not admin:
        emit('create_room_error', {'error': 'Faltan room o admin.'})
        return
    if room in chat_rooms:
        emit('create_room_error', {'error': 'Sala ya existe.'})
        return
    chat_rooms[room] = {
        'admin': admin,
        'users': set([admin]),
        'messages': []
    }
    emit('create_room_success', {'room': room}, broadcast=True)


@socketio.on('list_rooms')
def handle_list_rooms():
    rooms_list = [
        {'room': r, 'admin': d['admin'], 'user_count': len(d['users'])}
        for r, d in chat_rooms.items()
    ]
    emit('rooms_list', rooms_list)


@socketio.on('join_room')
def handle_join_room(data):
    room = data.get('room', '').strip()
    user = data.get('user', '').strip()
    if room not in chat_rooms:
        emit('join_room_error', {'error': 'Sala no existe.'})
        return
    chat_rooms[room]['users'].add(user)
    join_room(room)
    emit('join_room_success', {'room': room, 'user': user}, room=room)


@socketio.on('leave_room')
def handle_leave_room(data):
    room = data.get('room', '').strip()
    user = data.get('user', '').strip()
    if room in chat_rooms and user in chat_rooms[room]['users']:
        chat_rooms[room]['users'].remove(user)
        leave_room(room)
        emit('leave_room_success', {'room': room, 'user': user}, room=room)


@socketio.on('send_message')
def handle_send_message(data):
    room = data.get('room', '').strip()
    sender = data.get('sender', '').strip()
    message_text = data.get('message', '')
    if room not in chat_rooms:
        emit('send_message_error', {'error': 'Sala no existe.'})
        return
    if sender not in chat_rooms[room]['users']:
        emit('send_message_error', {'error': 'No estás en la sala.'})
        return
    msg = {
        'room': room,
        'sender': sender,
        'message': message_text,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    chat_rooms[room]['messages'].append(msg)
    emit('new_message', msg, room=room)


@socketio.on('get_messages')
def handle_get_messages(data):
    room = data.get('room', '').strip()
    if room not in chat_rooms:
        emit('get_messages_error', {'error': 'Sala no existe.'})
        return
    emit('messages_history', chat_rooms[room]['messages'])


@socketio.on('remove_user')
def handle_remove_user(data):
    room = data.get('room', '').strip()
    admin = data.get('admin', '').strip()
    user = data.get('user', '').strip()
    if room not in chat_rooms:
        emit('remove_user_error', {'error': 'Sala no existe.'})
        return
    if chat_rooms[room]['admin'] != admin:
        emit('remove_user_error', {'error': 'Sólo admin puede remover.'})
        return
    if user == admin or user not in chat_rooms[room]['users']:
        emit('remove_user_error', {'error': 'Usuario inválido.'})
        return
    chat_rooms[room]['users'].remove(user)
    emit('user_removed', {'room': room, 'user': user}, room=room)


########################################
# Arranque
########################################

if __name__ == '__main__':
    # Para producción podrías usar gunicorn + eventlet/gevent
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
