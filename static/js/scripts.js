// Initialisation du socket.io
const socket = io();

// Références des éléments du DOM
const chatDisplay = document.getElementById('chatDisplay');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const clearButton = document.getElementById('clearButton');
const onlineUsers = document.getElementById('onlineUsers');
const typingNotification = document.getElementById('typingNotification');

let currentUser = '';

// Fonction pour définir le nom d'utilisateur
function setUsername(username) {
    currentUser = username;
    socket.emit('username', username);
}

// Si `window.username` est défini, appelle `setUsername`
if (typeof window.username !== 'undefined') {
    setUsername(window.username);
}

// Envoyer un message
const sendMessage = () => {
    const message = messageInput.value;
    if (message.trim()) {
        socket.send(message);
        messageInput.value = '';
    }
};

sendButton.addEventListener('click', sendMessage);

// Effacer le message
clearButton.addEventListener('click', () => {
    messageInput.value = '';
});

// Notification de saisie
messageInput.addEventListener('input', () => {
    socket.emit('typing', { room: 'default' });
});

// Recevoir un message
socket.on('message', (msg) => {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message');
    if (msg.includes('a rejoint le chat') || msg.includes('a quitté le chat')) {
        messageElement.classList.add(msg.includes('a rejoint le chat') ? 'join-message' : 'leave-message');
        messageElement.textContent = msg;
    } else {
        const [sender, message] = msg.split(': ');
        messageElement.classList.add(sender === currentUser ? 'own-message' : 'other-message');
        const usernameElement = document.createElement('strong');
        usernameElement.textContent = sender + ': ';
        messageElement.appendChild(usernameElement);
        messageElement.appendChild(document.createTextNode(message));
    }
    chatDisplay.appendChild(messageElement);
    chatDisplay.scrollTop = chatDisplay.scrollHeight;
});

// Mettre à jour les utilisateurs en ligne
socket.on('user_online', (users) => {
    onlineUsers.innerHTML = '';
    users.forEach(user => {
        const userElement = document.createElement('div');
        userElement.textContent = user;
        onlineUsers.appendChild(userElement);
    });
});

// Notification de saisie d'un utilisateur
socket.on('typing', (data) => {
    typingNotification.textContent = `${data.username} est en train de taper...`;
    setTimeout(() => typingNotification.textContent = '', 3000);
});

// Notification de déconnexion d'un utilisateur
socket.on('user_disconnected', (username) => {
    const userElements = Array.from(onlineUsers.children);
    userElements.forEach(userElement => {
        if (userElement.textContent === username) {
            onlineUsers.removeChild(userElement);
        }
    });
});

