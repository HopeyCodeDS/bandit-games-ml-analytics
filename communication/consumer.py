import pika
import json


def receive_message_from_rabbitmq(queue_name):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue=queue_name)

    def callback(ch, method, properties, body):
        message = json.loads(body)
        print(f" [x] Received message from {queue_name}: {message}")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    print(f" [*] Waiting for messages in {queue_name}. To exit, press CTRL+C")
    channel.start_consuming()

# Example Usage
receive_message_from_rabbitmq('player_updates')
