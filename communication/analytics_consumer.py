# analytics_consumer.py
import json
import pika
import mysql.connector
from datetime import datetime
from typing import Dict, Any
import uuid
import logging
from dataclasses import dataclass
from mysql.connector import pooling

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DBConfig:
    host: str = "localhost"
    port: int = 3309
    user: str = "root"
    password: str = "root"
    database: str = "platform_analytics"
    pool_name: str = "analytics_pool"
    pool_size: int = 5


class DatabaseConnection:
    def __init__(self, config: DBConfig):
        self.dbconfig = {
            "host": config.host,
            "port": config.port,
            "user": config.user,
            "password": config.password,
            "database": config.database
        }
        self.pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name=config.pool_name,
            pool_size=config.pool_size,
            **self.dbconfig
        )

    def get_connection(self):
        return self.pool.get_connection()


class RabbitMQConnection:
    def __init__(self):
        self.connection = None
        self.channel = None

    def connect(self):
        # Connect to RabbitMQ
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        self.channel = self.connection.channel()

        # Declare exchanges
        self.channel.exchange_declare(
            exchange='data_analytics_exchange',
            exchange_type='topic',
            durable=True
        )
        self.channel.exchange_declare(
            exchange='user_signup_exchange',
            exchange_type='topic',
            durable=True
        )

        # Declare queues
        self.channel.queue_declare(queue='data_analytics_q', durable=True)
        self.channel.queue_declare(queue='user_signup_q', durable=True)

        # Bind queues
        self.channel.queue_bind(
            exchange='data_analytics_exchange',
            queue='data_analytics_q',
            routing_key='game.#'
        )
        self.channel.queue_bind(
            exchange='user_signup_exchange',
            queue='user_signup_q',
            routing_key='user.signup'
        )

    def close(self):
        if self.connection:
            self.connection.close()


class AnalyticsEventProcessor:
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def process_game_event(self, event_data: Dict[str, Any]) -> None:
        try:
            event_body = json.loads(event_data["eventBody"])
            logger.info(f"Processing game event for match {event_body['matchId']}")

            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Insert into match_history
                match_history_query = """
                INSERT INTO match_history (
                    match_id, game_id, player1_id, player2_id, winner_id,
                    start_time, end_time, duration_minutes, result
                ) VALUES (
                    UUID_TO_BIN(%s),
                    (SELECT game_id FROM games WHERE name = %s),
                    UUID_TO_BIN(%s),
                    UUID_TO_BIN(%s),
                    UUID_TO_BIN(%s),
                    %s, %s, %s, %s
                )
                """

                start_time = datetime.fromisoformat(event_body["startTime"].replace('Z', ''))
                end_time = datetime.fromisoformat(event_body["endTime"].replace('Z', ''))
                duration = int((end_time - start_time).total_seconds() / 60)

                result = 'win' if event_body["winnerId"] else 'draw'

                cursor.execute(match_history_query, (
                    event_body["matchId"],
                    event_body["game"],
                    event_body["player1Id"],
                    event_body["player2Id"],
                    event_body["winnerId"],
                    start_time,
                    end_time,
                    duration,
                    result
                ))

                # Insert match moves for both players
                moves_query = """
                INSERT INTO match_moves (
                    move_id, match_id, player_id, moves_count
                ) VALUES (
                    UUID_TO_BIN(%s),
                    UUID_TO_BIN(%s),
                    UUID_TO_BIN(%s),
                    %s
                )
                """

                # Player 1 moves
                cursor.execute(moves_query, (
                    str(uuid.uuid4()),
                    event_body["matchId"],
                    event_body["player1Id"],
                    event_body["player1MoveCounts"]
                ))

                # Player 2 moves
                cursor.execute(moves_query, (
                    str(uuid.uuid4()),
                    event_body["matchId"],
                    event_body["player2Id"],
                    event_body["player2MoveCounts"]
                ))

                # Update player game stats for both players
                for player_id in [event_body["player1Id"], event_body["player2Id"]]:
                    # Get game_id first
                    cursor.execute("SELECT game_id FROM games WHERE name = %s", (event_body["game"],))
                    game_id_result = cursor.fetchone()
                    if not game_id_result:
                        raise Exception(f"Game {event_body['game']} not found in database")

                    # Convert player_id to binary
                    cursor.execute("SELECT UUID_TO_BIN(%s)", (player_id,))
                    player_id_bin = cursor.fetchone()[0]

                    # Call stored procedure
                    cursor.callproc('update_player_game_stats', [player_id_bin, game_id_result[0]])

                conn.commit()
                logger.info(f"Successfully processed game event for match {event_body['matchId']}")

        except Exception as e:
            logger.error(f"Error processing game event: {str(e)}")
            raise

    def process_user_event(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info(f"Processing user event for {event_data['username']}")
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                insert_query = """
                INSERT INTO players (
                    player_id, username, firstname, lastname,
                    email, birthdate, gender, country
                ) VALUES (
                    UUID_TO_BIN(%s), %s, %s, %s, %s, %s, %s, %s
                )
                """

                cursor.execute(insert_query, (
                    event_data["player_id"],
                    event_data["username"],
                    event_data["firstname"],
                    event_data["lastname"],
                    event_data["email"],
                    event_data["birthdate"],
                    event_data["gender"],
                    event_data["country"]
                ))

                conn.commit()
                logger.info(f"Successfully processed user event for {event_data['username']}")

        except Exception as e:
            logger.error(f"Error processing user event: {str(e)}")
            raise


class AnalyticsConsumer:
    def __init__(self):
        self.db_config = DBConfig()
        self.db_connection = DatabaseConnection(self.db_config)
        self.rmq_connection = RabbitMQConnection()
        self.processor = AnalyticsEventProcessor(self.db_connection)

    def process_message(self, ch, method, properties, body):
        try:
            logger.info(f"Raw message received: {body}")
            message = json.loads(body)
            routing_key = method.routing_key
            logger.info(f"Received message with routing key: {routing_key}")
            logger.info(f"Decoded message content: {message}")

            if routing_key.startswith('game.'):
                logger.info("Processing as game event")
                self.processor.process_game_event(message)
            elif routing_key == 'user.signup':
                logger.info("Processing as user signup event")
                self.processor.process_user_event(message)

            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info("Message processed successfully")

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            # Don't requeue messages with validation errors
            if "foreign key constraint fails" in str(e):
                logger.error("Foreign key constraint failed - discarding message")
                ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            else:
                # Only requeue for other types of errors
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start(self):
        try:
            logger.info("Starting Analytics Consumer...")
            self.rmq_connection.connect()

            # Set up consumers
            self.rmq_connection.channel.basic_consume(
                queue='data_analytics_q',
                on_message_callback=self.process_message
            )
            self.rmq_connection.channel.basic_consume(
                queue='user_signup_q',
                on_message_callback=self.process_message
            )

            logger.info("Consumer ready, waiting for messages...")
            self.rmq_connection.channel.start_consuming()

        except KeyboardInterrupt:
            logger.info("Shutting down consumer...")
            self.rmq_connection.channel.stop_consuming()
        finally:
            self.rmq_connection.close()


def main():
    consumer = AnalyticsConsumer()
    consumer.start()


if __name__ == "__main__":
    main()