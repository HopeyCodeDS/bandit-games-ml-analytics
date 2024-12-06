import pika
import json
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GameStatisticsListener:
    def __init__(self):
        # RabbitMQ connection parameters
        self.connection_params = pika.ConnectionParameters(
            host='localhost',
            port=5672,
            credentials=pika.PlainCredentials('guest', 'guest')
        )

        self.queue_name = 'data_analytics_q'
        self.connection = None
        self.channel = None

    def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = pika.BlockingConnection(self.connection_params)
            self.channel = self.connection.channel()

            # Declare the exchange and queue with durable=True to match Java configuration
            self.channel.exchange_declare(
                exchange='data_analytics_exchange',
                exchange_type='direct',
                durable=True  # Changed to True to match Java config
            )

            self.channel.queue_declare(
                queue=self.queue_name,
                durable=False  # Keep as false since your Java config has it as false
            )

            # Bind the queue to the exchange
            self.channel.queue_bind(
                exchange='data_analytics_exchange',
                queue=self.queue_name,
                routing_key='game.over'
            )

            logger.info("Successfully connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise

    def process_message(self, ch, method, properties, body):
        """Process the received message"""
        try:
            # Parse the message
            message = json.loads(body)
            event_header = message.get('eventHeader', {})
            event_body = json.loads(message.get('eventBody', '{}'))

            logger.info("Received game statistics event:")
            logger.info(f"Event ID: {event_header.get('eventID')}")
            logger.info(f"Event Type: {event_header.get('eventType')}")
            logger.info("\nGame Details:")
            logger.info(f"Match ID: {event_body.get('matchId')}")
            logger.info(f"Game: {event_body.get('game')}")
            logger.info(f"Player 1 ID: {event_body.get('player1Id')}")
            logger.info(f"Player 2 ID: {event_body.get('player2Id')}")
            logger.info(f"Winner ID: {event_body.get('winnerId')}")
            logger.info(f"Start Time: {event_body.get('startTime')}")
            logger.info(f"End Time: {event_body.get('endTime')}")
            logger.info(f"Player 1 Moves: {event_body.get('player1MoveCounts')}")
            logger.info(f"Player 2 Moves: {event_body.get('player2MoveCounts')}")

            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag)

    def start_listening(self):
        """Start listening for messages"""
        try:
            # Set up quality of service
            self.channel.basic_qos(prefetch_count=1)

            # Set up the consumer
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self.process_message
            )

            logger.info(f"Started listening on queue: {self.queue_name}")
            logger.info("To exit press CTRL+C")

            # Start consuming messages
            self.channel.start_consuming()

        except KeyboardInterrupt:
            logger.info("Stopping the listener...")
            self.channel.stop_consuming()
        except Exception as e:
            logger.error(f"Error while listening: {str(e)}")
        finally:
            if self.connection and not self.connection.is_closed:
                self.connection.close()


if __name__ == "__main__":
    listener = GameStatisticsListener()
    try:
        listener.connect()
        listener.start_listening()
    except Exception as e:
        logger.error(f"Failed to start listener: {str(e)}")