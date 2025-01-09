import pika

print("Attempting to connect to RabbitMQ...")
try:
    # Try explicit connection parameters
    credentials = pika.PlainCredentials('guest', 'guest')
    parameters = pika.ConnectionParameters(
        host='localhost',
        port=5672,
        virtual_host='/',
        credentials=credentials
    )

    connection = pika.BlockingConnection(parameters)
    print("Successfully connected to RabbitMQ!")

    channel = connection.channel()
    print("Successfully created channel!")

    # List existing exchanges
    print("\nListing exchanges:")
    exchanges = channel.exchange_declare(exchange='order', passive=True)
    print("Found 'order' exchange")

    # List existing queues
    print("\nListing queues:")
    queues = channel.queue_declare(queue='order_report', passive=True)
    print("Found 'order_report' queue")

    connection.close()
    print("\nConnection test completed successfully!")

except pika.exceptions.AMQPConnectionError as e:
    print(f"Connection Error: {e}")
except pika.exceptions.AMQPChannelError as e:
    print(f"Channel Error: {e}")
except Exception as e:
    print(f"Unexpected error: {type(e).__name__} - {e}")