import pika
import json

def send_message_to_rabbitmq(queue_name, message):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue=queue_name)
    channel.basic_publish(exchange='', routing_key=queue_name, body=json.dumps(message))
    print(f" [x] Sent message to {queue_name}: {message}")

    connection.close()

# Example Usage
message = {
    "playerId": "player1",
    "gameId": "game1",
    "moves": 15,
    "duration": 120,
    "result": "Win",
    "timestamp": "2024-11-18T10:00:00"
}
send_message_to_rabbitmq('game_stats', message)
