import pika
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BattleshipMatchSubscriber:
    def __init__(self):
        self.queue_name = 'battleship_queue'
        self.exchange_name = 'battleship_exchange'
        self.routing_key = 'match.completed'
        self.connection = None
        self.channel = None

    def connect(self):
        try:
            credentials = pika.PlainCredentials('guest', 'guest')
            parameters = pika.ConnectionParameters(
                host='localhost',
                port=5672,
                credentials=credentials
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Setup exchange and queue
            self.channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type='direct',
                durable=True
            )

            self.channel.queue_declare(
                queue=self.queue_name,
                durable=True
            )

            self.channel.queue_bind(
                queue=self.queue_name,
                exchange=self.exchange_name,
                routing_key=self.routing_key
            )

            logger.info("Successfully connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Error connecting to RabbitMQ: {str(e)}")
            raise

    def process_match_data(self, ch, method, properties, body):
        try:
            match_data = json.loads(body)

            # Calculate game duration
            start_time = datetime.fromisoformat(match_data['startTime'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(match_data['endTime'].replace('Z', '+00:00'))
            duration = end_time - start_time

            # Analyze and log match data
            logger.info("Match Analysis:")
            logger.info(f"Match ID: {match_data['matchId']}")
            logger.info(f"Game ID: {match_data['gameId']}")
            logger.info(f"Duration: {duration}")
            logger.info(f"Winner: {match_data['winnerId']}")
            logger.info(f"Player 1 moves: {match_data['player1MoveCounts']}")
            logger.info(f"Player 2 moves: {match_data['player2MoveCounts']}")

            # Calculate efficiency (moves per ship sunk - assuming 5 ships)
            winner_moves = (match_data['player1MoveCounts']
                            if match_data['winnerId'] == match_data['player1Id']
                            else match_data['player2MoveCounts'])
            efficiency = winner_moves / 5  # 5 ships
            logger.info(f"Winner's moves per ship: {efficiency:.2f}")

            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.error(f"Error processing match data: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag)

    def start_consuming(self):
        try:
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self.process_match_data
            )

            logger.info("Started consuming messages. Waiting for match data...")
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
    subscriber = BattleshipMatchSubscriber()
    try:
        subscriber.connect()
        subscriber.start_consuming()
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {str(e)}")