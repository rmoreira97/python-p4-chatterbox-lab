from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_socketio import SocketIO, emit
from os import urandom

from models import db, Message

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = urandom(24)  # Generates a random 24-byte long secret key


CORS(app)
migrate = Migrate(app, db)
socketio = SocketIO(app, cors_allowed_origins="*")

db.init_app(app)

@app.route('/messages', methods=['GET', 'POST'])
def messages():
    if request.method == 'GET':
        all_messages = Message.query.all()
        return jsonify([message.serialize() for message in all_messages])
    elif request.method == 'POST':
        data = request.json
        new_message = Message(body=data['body'], username=data['username'])
        db.session.add(new_message)
        db.session.commit()
        socketio.emit('new_message', new_message.serialize(), broadcast=True)
        return jsonify(new_message.serialize()), 201
@app.route('/messages/<int:message_id>', methods=['PUT', 'DELETE'])
def handle_message(message_id):
    message = Message.query.get(message_id)
    if not message:
        return jsonify({"error": "Message not found"}), 404

    if request.method == 'PUT':
        data = request.json
        message.body = data['body']
        db.session.commit()
        socketio.emit('update_message', message.serialize(), broadcast=True)
        return jsonify(message.serialize())

    elif request.method == 'DELETE':
        db.session.delete(message)
        db.session.commit()
        socketio.emit('delete_message', message.id, broadcast=True)
        return jsonify({"message": "Deleted successfully"}), 200
@app.route('/messages/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    message = Message.query.get(message_id)
    if not message:
        return jsonify({"error": "Message not found"}), 404

    db.session.delete(message)
    db.session.commit()
    socketio.emit('delete_message', message.id, broadcast=True)
    return jsonify({"message": "Deleted successfully"}), 200


@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, port=5555)
