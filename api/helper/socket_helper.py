# from flask import current_app
# from flask_socketio import SocketIO, send, emit

# try:
#     from main import app, socketio
# except:
#     from moov_backend.main import app


# def ack():
#     print 'message was received!'


# def handle_my_custom_event(json):
#     # with app.app_context():
#     emit('my response', json, callback=ack)

# socketio.on_event('my event', handle_my_custom_event, namespace='/test')
