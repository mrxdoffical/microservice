import json
from channels.generic.websocket import WebsocketConsumer
import logging

logger = logging.getLogger(__name__)

class ProgressConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        logger.debug('WebSocket connection established')

    def disconnect(self, close_code):
        logger.debug('WebSocket connection closed')

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        self.send(text_data=json.dumps({
            'message': message
        }))
        logger.debug(f'Received message: {message}')

    def send_progress(self, event):
        progress = event['progress']
        self.send(text_data=json.dumps({
            'progress': progress
        }))
        logger.debug(f'Sent progress: {progress}')