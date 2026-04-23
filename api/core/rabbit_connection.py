import pika
import os
import json

class RabbitMQClient:
    def __init__(self):
        credentials = pika.PlainCredentials(
            os.getenv("RABBITMQ_USER"),
            os.getenv("RABBITMQ_PASSWORD")
        )
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=os.getenv("RABBITMQ_HOST"),
                port=5672,
                virtual_host='/',
                credentials=credentials,
                socket_timeout=5,
                blocked_connection_timeout=5
            )
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='email')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def publish(self, message: dict):
        self.channel.basic_publish(
            exchange='',
            routing_key='email',
            body=json.dumps(message)
        )

    def close(self):
        if self.connection and self.connection.is_open:
            self.connection.close()