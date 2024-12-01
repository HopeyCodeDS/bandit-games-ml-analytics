# import pika
# import json
# import time
# import sys
#
#
# def connect():
#     try:
#         print(" [*] Connecting to RabbitMQ...")
#         connection = pika.BlockingConnection(pika.ConnectionParameters(
#             host='localhost',
#             heartbeat=600,
#             blocked_connection_timeout=300
#         ))
#         channel = connection.channel()
#         print(" [*] Connected successfully")
#         return connection, channel
#     except Exception as e:
#         print(f"Connection failed: {e}")
#         return None, None
#
#
# def setup_queue(channel):
#     # Declare exchange
#     channel.exchange_declare(
#         exchange='order',
#         exchange_type='direct',
#         durable=False
#     )
#
#     # Declare queue
#     queue = channel.queue_declare(
#         queue='order_report',
#         durable=False,
#         exclusive=False,
#         auto_delete=False
#     )
#     queue_name = queue.method.queue
#
#     # Create binding
#     channel.queue_bind(
#         exchange='order',
#         queue=queue_name,
#         routing_key='order.report'
#     )
#
#     return queue_name
#
#
# def callback(ch, method, properties, body):
#     try:
#         print("\n [x] Received message")
#         print(f"Raw message: {body}")  # Debug print
#
#         payload = json.loads(body)
#         print(' [x] Generating report')
#         print(f"""
#         ID: {payload.get('id')}
#         User Email: {payload.get('userEmail', payload.get('user_email'))}
#         Product: {payload.get('product')}
#         Quantity: {payload.get('quantity')}
#         """)
#         print(' [x] Done')
#         ch.basic_ack(delivery_tag=method.delivery_tag)
#     except Exception as e:
#         print(f"Error processing message: {e}")
#         print(f"Message body: {body}")
#         ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
#
#
# def main():
#     while True:
#         try:
#             connection, channel = connect()
#             if not connection or not channel:
#                 print("Could not connect. Retrying in 5 seconds...")
#                 time.sleep(5)
#                 continue
#
#             queue_name = setup_queue(channel)
#
#             # Set prefetch count
#             channel.basic_qos(prefetch_count=1)
#
#             # Start consuming
#             channel.basic_consume(
#                 queue=queue_name,
#                 on_message_callback=callback
#             )
#
#             print(' [*] Waiting for report messages. To exit press CTRL+C')
#             channel.start_consuming()
#
#         except KeyboardInterrupt:
#             print("\nShutting down...")
#             if connection and not connection.is_closed:
#                 connection.close()
#             sys.exit(0)
#         except Exception as e:
#             print(f"Error occurred: {e}")
#             print("Reconnecting in 5 seconds...")
#             time.sleep(5)
#             continue
#
#
# if __name__ == "__main__":
#     main()

import pika
import json
import sys


def callback(ch, method, properties, body):
    try:
        print("\n [x] Received message")
        print(f"Raw message: {body}")
        payload = json.loads(body)
        print(' [x] Generating report')
        print(f"""
        ID: {payload.get('id')}
        User Email: {payload.get('userEmail', payload.get('user_email'))}
        Product: {payload.get('product')}
        Quantity: {payload.get('quantity')}
        """)
        print(' [x] Done')
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing message: {e}")
        print(f"Message body: {body}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    try:
        # Connection setup
        credentials = pika.PlainCredentials('guest', 'guest')
        parameters = pika.ConnectionParameters(
            host='localhost',
            port=5672,
            virtual_host='/',
            credentials=credentials
        )

        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        print(" [*] Connected to RabbitMQ")

        # Get existing queue
        result = channel.queue_declare(
            queue='order_report',
            durable=False,
            exclusive=False,
            auto_delete=False
        )
        queue_name = result.method.queue
        print(f" [*] Queue: {queue_name}")

        # Set up consumer
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback
        )

        print(' [*] Waiting for messages. To exit press CTRL+C')
        channel.start_consuming()

    except KeyboardInterrupt:
        print("Shutting down...")
        try:
            channel.close()
            connection.close()
        except:
            pass
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()