import pika
import json
import uuid
import mysql.connector
from datetime import datetime, timedelta
import time
import logging
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestEventPublisher:
    def __init__(self):
        # Get configuration from environment variables
        self.rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
        self.rabbitmq_port = int(os.getenv('RABBITMQ_PORT', '5672'))
        self.rabbitmq_user = os.getenv('RABBITMQ_USERNAME', 'guest')
        self.rabbitmq_pass = os.getenv('RABBITMQ_PASSWORD', 'guest')

        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = int(os.getenv('DB_PORT', '3306'))
        self.db_user = os.getenv('DB_USER', 'root')
        self.db_pass = os.getenv('DB_PASSWORD', 'root')
        self.db_name = os.getenv('DB_NAME', 'platform_analytics')
        self.db_ssl_ca = os.getenv('DB_SSL_CA', '')

        # Initialize connections
        self._init_rabbitmq()
        self._init_database()

    def _init_rabbitmq(self):
        """Initialize RabbitMQ connection with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                credentials = pika.PlainCredentials(self.rabbitmq_user, self.rabbitmq_pass)
                parameters = pika.ConnectionParameters(
                    host=self.rabbitmq_host,
                    port=self.rabbitmq_port,
                    credentials=credentials,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
                self.connection = pika.BlockingConnection(parameters)
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
                logger.info(f"Successfully connected to RabbitMQ at {self.rabbitmq_host}")
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"RabbitMQ connection attempt {attempt + 1} failed: {str(e)}")
                time.sleep(2)

    def _init_database(self):
        """Initialize database connection with SSL support"""
        config = {
            "host": self.db_host,
            "port": self.db_port,
            "user": self.db_user,
            "password": self.db_pass,
            "database": self.db_name
        }

        # Add SSL configuration if specified
        if self.db_ssl_ca:
            config.update({
                "ssl": {
                    "ca": self.db_ssl_ca
                }
            })

        self.db = mysql.connector.connect(**config)
        self.cursor = self.db.cursor(buffered=True)
        logger.info(f"Successfully connected to database at {self.db_host}")

    def _refresh_db_connection(self):
        """Refresh database connection"""
        try:
            self.db.close()
        except:
            pass
        self._init_database()

    def ensure_game_exists(self) -> Optional[bytes]:
        """Ensure test game exists in the database and return its ID"""
        try:
            self._refresh_db_connection()

            # First check if game exists
            self.cursor.execute("SELECT game_id FROM games WHERE name = 'battleship'")
            result = self.cursor.fetchone()

            if result:
                logger.info("✓ Test game found")
                return result[0]

            # If not exists, create it
            game_id = str(uuid.uuid4())
            self.cursor.execute("""
                INSERT INTO games (game_id, name, description, rules, can_draw)
                VALUES (UUID_TO_BIN(%s), 'battleship', 'Battleship game', 'Standard rules', 0)
            """, (game_id,))
            self.db.commit()
            logger.info("✓ Test game created")

            return self.cursor.lastrowid

        except Exception as e:
            logger.error(f"Error ensuring game exists: {str(e)}")
            raise

    def create_test_player(self, username_prefix="testuser", max_retries=3) -> Optional[str]:
        """Create a test player and return their ID"""
        player_id = str(uuid.uuid4())
        user_event = {
            "player_id": player_id,
            "username": f"{username_prefix}_{player_id[:8]}",
            "firstname": "Test",
            "lastname": "User",
            "email": f"{username_prefix}_{player_id[:8]}@gmail.com",
            "birthdate": "1997-04-01",
            "gender": "Male",
            "country": "Russia"
        }

        message_body = json.dumps(user_event)
        logger.info(f"Publishing user signup event: {message_body}")

        try:
            self.channel.basic_publish(
                exchange='user_signup_exchange',
                routing_key='user.signup',
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2  # Make message persistent
                )
            )
            logger.info(f"✓ Published user event for: {user_event['username']}")

            # Verify creation
            for attempt in range(max_retries):
                time.sleep(2)
                if self.verify_user_creation(player_id):
                    return player_id
                logger.info(f"User verification attempt {attempt + 1}/{max_retries}")

            return None
        except Exception as e:
            logger.error(f"Error creating test player: {str(e)}")
            return None

    def publish_game_event(self, player1_id: str, player2_id: str, max_retries=3) -> Optional[str]:
        """Publish a game event and verify its processing"""
        match_id = str(uuid.uuid4())
        game_event = {
            "matchId": match_id,
            "game": "battleship",
            "player1Id": player1_id,
            "player2Id": player2_id,
            "startTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "endTime": (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S"),
            "player1MoveCounts": 10,
            "player2MoveCounts": 9,
            "winnerId": player1_id
        }

        try:
            self.channel.basic_publish(
                exchange='data_analytics_exchange',
                routing_key='game.over',
                body=json.dumps(game_event),
                properties=pika.BasicProperties(
                    delivery_mode=2
                )
            )
            logger.info(f"✓ Published game event: {match_id}")

            # Verify processing
            for attempt in range(max_retries):
                time.sleep(2)
                if self.verify_game_record(match_id):
                    return match_id
                logger.info(f"Game verification attempt {attempt + 1}/{max_retries}")

            return None
        except Exception as e:
            logger.error(f"Error publishing game event: {str(e)}")
            return None

    def verify_user_creation(self, user_id: str) -> bool:
        """Verify that the user was created in the database"""
        try:
            self._refresh_db_connection()

            query = """
            SELECT BIN_TO_UUID(player_id) as player_id, username 
            FROM players 
            WHERE player_id = UUID_TO_BIN(%s)
            """
            self.cursor.execute(query, (user_id,))
            result = self.cursor.fetchone()

            if result:
                logger.info(f"✓ User verified in database: {result}")
                return True

            logger.info("User not found, checking recent entries...")
            self.cursor.execute("""
                SELECT BIN_TO_UUID(player_id) as player_id, username 
                FROM players 
                ORDER BY created_at DESC 
                LIMIT 3
            """)
            recent = self.cursor.fetchall()
            logger.info(f"Recent users: {recent}")
            return False

        except Exception as e:
            logger.error(f"Error verifying user: {str(e)}")
            return False

    def verify_game_record(self, match_id: str) -> bool:
        """Verify that the game record was created in the database"""
        try:
            self._refresh_db_connection()

            query = """
            SELECT 
                BIN_TO_UUID(match_id) as match_id,
                BIN_TO_UUID(player1_id) as player1_id,
                BIN_TO_UUID(player2_id) as player2_id
            FROM match_history 
            WHERE match_id = UUID_TO_BIN(%s)
            """
            self.cursor.execute(query, (match_id,))
            result = self.cursor.fetchone()

            if result:
                logger.info(f"✓ Game record verified: {result}")
                return True

            logger.info("Game not found, checking recent entries...")
            return False

        except Exception as e:
            logger.error(f"Error verifying game record: {str(e)}")
            return False

    def run_test_scenario(self):
        """Run a complete test scenario"""
        try:
            logger.info("=== Starting Test Scenario ===")

            # 1. Ensure test game exists
            logger.info("\n1. Creating test game...")
            game_id = self.ensure_game_exists()
            if not game_id:
                raise Exception("Failed to create test game")

            # 2. Create test players
            logger.info("\n2. Creating test players...")
            player1_id = self.create_test_player("player1")
            if not player1_id:
                raise Exception("Failed to create player1")

            player2_id = self.create_test_player("player2")
            if not player2_id:
                raise Exception("Failed to create player2")

            # 3. Publish game event
            logger.info("\n3. Publishing game event...")
            match_id = self.publish_game_event(player1_id, player2_id)
            if not match_id:
                raise Exception("Failed to create game record")

            logger.info("\n=== Test Scenario Completed Successfully! ===")

        except Exception as e:
            logger.error(f"\n❌ Test scenario failed: {str(e)}")
        finally:
            try:
                self.connection.close()
                self.db.close()
            except:
                pass


def main():
    publisher = TestEventPublisher()
    publisher.run_test_scenario()


if __name__ == "__main__":
    main()