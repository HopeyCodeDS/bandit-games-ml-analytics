import pika

QUEUE_NAME = 'game_data_queue'

def callback(ch, method, properties, body):
    print(f"Received message: {body.decode()}")

def main():
    # Establish connection
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declare queue
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    # Consume messages
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)

    print("Waiting for messages. To exit, press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    main()
