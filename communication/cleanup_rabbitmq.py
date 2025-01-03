# cleanup_rabbitmq.py
import pika

def cleanup_rabbitmq():
    # Connect to RabbitMQ
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost')
    )
    channel = connection.channel()

    try:
        # Delete queues
        queues_to_delete = ['data_analytics_q', 'user_signup_q']
        for queue in queues_to_delete:
            try:
                channel.queue_delete(queue=queue)
                print(f"✓ Deleted queue: {queue}")
            except Exception as e:
                print(f"! Could not delete queue {queue}: {str(e)}")

        # Delete exchanges
        exchanges_to_delete = ['data_analytics_exchange', 'user_signup_exchange']
        for exchange in exchanges_to_delete:
            try:
                channel.exchange_delete(exchange=exchange)
                print(f"✓ Deleted exchange: {exchange}")
            except Exception as e:
                print(f"! Could not delete exchange {exchange}: {str(e)}")

        print("\nCleanup completed successfully!")
    finally:
        connection.close()

if __name__ == "__main__":
    print("Starting RabbitMQ cleanup...")
    cleanup_rabbitmq()