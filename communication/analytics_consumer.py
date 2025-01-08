import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any

import mysql.connector
import pika
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DBConfig:
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', '3306'))
    user: str = os.getenv('DB_USER', 'root')
    password: str = os.getenv('DB_PASSWORD', 'root')
    database: str = os.getenv('DB_NAME', 'platform_analytics')
    pool_name: str = "analytics_pool"
    pool_size: int = 5
    ssl_mode: str = os.getenv('DB_SSL_MODE', '')
    ssl_ca: str = os.getenv('DB_SSL_CA', '')


class DatabaseConnection:
    def __init__(self, config: DBConfig):
        self.dbconfig = {
            "host": config.host,
            "port": config.port,
            "user": config.user,
            "password": config.password,
            "database": config.database
        }

        # Add SSL configuration if SSL mode is specified
        if config.ssl_mode:
            self.dbconfig.update({
                "ssl_mode": config.ssl_mode,
                "ssl_ca": config.ssl_ca
            })

        logger.info(f"Connecting to database at {config.host}:{config.port}")
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
            routing_key='game.over'  # Updated routing key
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
            logger.info(f"Processing game event for match {event_data['matchId']}")

            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT game_id FROM games WHERE name = %s", (event_data["game"],))
                game_result = cursor.fetchone()
                if not game_result:
                    raise Exception(f"Game {event_data['game']} not found")

                match_history_query = """
                INSERT INTO match_history (
                    match_id, game_id, player1_id, player2_id, winner_id,
                    start_time, end_time, duration_minutes, result
                ) VALUES (
                    UUID_TO_BIN(%s), %s, UUID_TO_BIN(%s), UUID_TO_BIN(%s), UUID_TO_BIN(%s),
                    %s, %s, %s, %s
                )"""

                start_time = datetime.strptime(event_data["startTime"], "%Y-%m-%dT%H:%M:%S")
                end_time = datetime.strptime(event_data["endTime"], "%Y-%m-%dT%H:%M:%S")
                duration = int((end_time - start_time).total_seconds() / 60)

                cursor.execute(match_history_query, (
                    event_data["matchId"],
                    game_result[0],
                    event_data["player1Id"],
                    event_data["player2Id"],
                    event_data["winnerId"],
                    start_time,
                    end_time,
                    duration,
                    'win' if event_data["winnerId"] else 'draw'
                ))

                moves_query = """
                INSERT INTO match_moves (move_id, match_id, player_id, moves_count)
                VALUES (UUID_TO_BIN(%s), UUID_TO_BIN(%s), UUID_TO_BIN(%s), %s)
                """

                cursor.execute(moves_query, (
                    str(uuid.uuid4()),
                    event_data["matchId"],
                    event_data["player1Id"],
                    event_data["player1MoveCounts"]
                ))
                cursor.execute(moves_query, (
                    str(uuid.uuid4()),
                    event_data["matchId"],
                    event_data["player2Id"],
                    event_data["player2MoveCounts"]
                ))

                stats_query = """
                CALL update_player_game_stats(UUID_TO_BIN(%s), %s)
                """

                for player_id in [event_data["player1Id"], event_data["player2Id"]]:
                    cursor.execute(stats_query, (player_id, game_result[0]))

                conn.commit()
                logger.info(f"Successfully processed game event for match {event_data['matchId']}")

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