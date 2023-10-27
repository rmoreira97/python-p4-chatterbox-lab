from flask import Flask, request, make_response, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'PibCRONMHEDlWbcVzEgCOD1y9Gy9Nc7W'  # Replace with your secret key
CORS(app)
socketio = SocketIO(app)

db = SQLAlchemy(app)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def serialize(self):
        return {
            'id': self.id,
            'body': self.body,
            'username': self.username,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

@app.get('/messages')
def get_messages():
    msgs = Message.query.order_by(Message.created_at).all()
    body = [m.serialize() for m in msgs]
    return body, 200

@app.post('/messages')
def post_messages():
    msg_data = request.get_json()
    if 'body' not in msg_data or 'username' not in msg_data:
        return make_response(jsonify({"error": "Body and username are required"}), 400)

    new_msg = Message(
        body=msg_data.get('body'),
        username=msg_data.get('username')
    )
    db.session.add(new_msg)
    db.session.commit()

    # Emit the new message to all connected clients
    emit('new_message', new_msg.serialize(), broadcast=True)

    return new_msg.serialize(), 201

@app.delete('/messages/<int:id>')
def delete_message(id):
    msg = Message.query.filter(Message.id == id).first()

    if msg is None:
        return {'message': 'message not found'}, 404

    db.session.delete(msg)
    db.session.commit()

    return {}, 200

@app.patch('/messages/<int:id>')
def patch_message(id):
    msg = Message.query.filter(Message.id == id).first()

    if msg is None:
        return {'message': 'message not found'}, 404

    msg_data = request.get_json()

    for field in msg_data:
        setattr(msg, field, msg_data[field])

    db.session.add(msg)
    db.session.commit()

    return msg.serialize(), 200

@app.route('/messages/<int:id>')
def messages_by_id(id):
    msg = Message.query.filter(Message.id == id).first()

    if msg is None:
        return {'message': 'message not found'}, 404

    return msg.serialize(), 200

@socketio.on('message')
def handle_message(data):
    # Save the message to the database
    new_msg = Message(body=data['body'], username=data['username'])
    db.session.add(new_msg)
    db.session.commit()

    # Emit the new message to all connected clients
    emit('new_message', new_msg.serialize(), broadcast=True)

if __name__ == '__main__':
    socketio.run(app, port=5000)
