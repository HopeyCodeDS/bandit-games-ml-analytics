import pika
import json

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

message = {
    "id": "test123",
    "userEmail": "test@example.com",
    "product": "Test Product",
    "quantity": 1
}

channel.basic_publish(
    exchange='order',
    routing_key='order.report',
    body=json.dumps(message),
    properties=pika.BasicProperties(
        content_type='application/json'
    )
)

print(" [x] Sent test message")
connection.close()