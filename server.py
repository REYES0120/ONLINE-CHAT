import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_socketio import SocketIO, send, join_room, leave_room, emit
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
socketio = SocketIO(app, cors_allowed_origins="*")

clients = {}

# Charger les utilisateurs à partir d'un fichier JSON
def load_users():
    try:
        with open('users.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Enregistrer les utilisateurs dans un fichier JSON
def save_users(users):
    with open('users.json', 'w') as file:
        json.dump(users, file)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        if username in users:
            flash('Le nom d\'utilisateur existe déjà.', 'danger')
            return redirect(url_for('register'))
        users[username] = generate_password_hash(password, method='pbkdf2:sha256')
        save_users(users)
        flash('Inscription réussie! Vous pouvez vous connecter maintenant.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        if username not in users or not check_password_hash(users[username], password):
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'danger')
            return redirect(url_for('login'))
        session['username'] = username
        return redirect(url_for('chat'))
    return render_template('login.html')

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', username=session['username'])

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@socketio.on('connect')
def handle_connect():
    print("Un utilisateur s'est connecté")

@socketio.on('disconnect')
def handle_disconnect():
    username = clients.pop(request.sid, "Un utilisateur")
    send(f"{username} a quitté le chat!", broadcast=True)
    emit('user_disconnected', username, broadcast=True)

@socketio.on('username')
def handle_username(username):
    clients[request.sid] = username
    send(f"{username} a rejoint le chat!", broadcast=True)
    emit('user_online', list(clients.values()), broadcast=True)

@socketio.on('message')
def handle_message(message):
    username = clients.get(request.sid, "Un utilisateur")
    send(f"{username}: {message}", broadcast=True)

@socketio.on('private_message')
def handle_private_message(data):
    recipient_sid = data['recipient_sid']
    message = data['message']
    send(f"Message privé de {clients.get(request.sid, 'Un utilisateur')}: {message}", to=recipient_sid)

@socketio.on('join')
def handle_join(data):
    username = clients.get(request.sid, "Un utilisateur")
    room = data['room']
    join_room(room)
    send(f"{username} a rejoint la salle {room}", to=room)

@socketio.on('leave')
def handle_leave(data):
    username = clients.get(request.sid, "Un utilisateur")
    room = data['room']
    leave_room(room)
    send(f"{username} a quitté la salle {room}", to=room)

@socketio.on('typing')
def handle_typing(data):
    username = clients.get(request.sid, "Un utilisateur")
    emit('typing', {'username': username}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=12345)

