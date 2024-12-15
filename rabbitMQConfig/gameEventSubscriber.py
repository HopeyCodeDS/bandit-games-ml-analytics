import pika
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GameEventSubscriber:
    def __init__(self):
        self.queue_name = 'data_analytics_q'
        self.exchange_name = 'data_analytics_exchange'
        self.routing_key = 'game.over'
        self.connection = None
        self.channel = None

    def connect(self):
        try:
            # Connect to RabbitMQ
            credentials = pika.PlainCredentials('guest', 'guest')  # Replace with your credentials
            parameters = pika.ConnectionParameters(
                host='localhost',  # Replace with your host
                port=5672,  # Replace with your port
                credentials=credentials
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Declare exchange and queue
            self.channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type='direct',
                durable=True
            )

            self.channel.queue_declare(
                queue=self.queue_name,
                durable=True
            )

            # Bind queue to exchange
            self.channel.queue_bind(
                queue=self.queue_name,
                exchange=self.exchange_name,
                routing_key=self.routing_key
            )

            logger.info("Successfully connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Error connecting to RabbitMQ: {str(e)}")
            raise

    def process_message(self, ch, method, properties, body):
        try:
            # Decode JSON message
            game_event = json.loads(body)

            logger.info(f"Received game event: {game_event}")

            # Process the game event
            self.analyze_game_data(game_event)

            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding message: {str(e)}")
            # Negative acknowledgment for invalid messages
            ch.basic_nack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            # Negative acknowledgment for processing errors
            ch.basic_nack(delivery_tag=method.delivery_tag)

    def analyze_game_data(self, game_event):
        """
        Analyze the game data - implement your analytics logic here
        """
        logger.info(f"Analyzing game data:")
        logger.info(f"Game ID: {game_event.get('gameId')}")
        logger.info(f"Player ID: {game_event.get('playerId')}")
        logger.info(f"Score: {game_event.get('score')}")
        logger.info(f"Timestamp: {game_event.get('timestamp')}")
        # Add your analytics logic here

    def start_consuming(self):
        try:
            # Set up quality of service
            self.channel.basic_qos(prefetch_count=1)

            # Start consuming messages
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self.process_message
            )

            logger.info("Started consuming messages. Waiting for game events...")
            self.channel.start_consuming()

        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
            self.channel.stop_consuming()
        except Exception as e:
            logger.error(f"Error in consumer: {str(e)}")
        finally:
            if self.connection and not self.connection.is_closed:
                self.connection.close()


if __name__ == "__main__":
    subscriber = GameEventSubscriber()
    try:
        subscriber.connect()
        subscriber.start_consuming()
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {str(e)}")