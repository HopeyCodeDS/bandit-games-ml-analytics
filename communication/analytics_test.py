import pika
import json
import uuid
import mysql.connector
from datetime import datetime, timedelta
import time
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestEventPublisher:
    def __init__(self):
        # RabbitMQ connection
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

        # Database connection
        self.db = mysql.connector.connect(
            host="localhost",
            port=3309,
            user="root",
            password="root",
            database="platform_analytics"
        )
        self.cursor = self.db.cursor(buffered=True)

    def ensure_game_exists(self) -> Optional[bytes]:
        """Ensure test game exists in the database and return its ID"""
        try:
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

            self.cursor.execute("SELECT game_id FROM games WHERE name = 'battleship'")
            return self.cursor.fetchone()[0]

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
            "email": f"{username_prefix}_{player_id[:8]}@example.com",
            "birthdate": "1990-01-01",
            "gender": "Male",
            "country": "TestCountry"
        }

        # Log the message we're about to send
        message_body = json.dumps(user_event)
        logger.info(f"Preparing to send user event: {message_body}")
        logger.info(f"Exchange: user_signup_exchange, Routing key: user.signup")

        self.channel.basic_publish(
            exchange='user_signup_exchange',
            routing_key='user.signup',
            body=message_body
        )
        logger.info(f"Published user event: {user_event['username']}")

        # Wait and verify with retries
        for attempt in range(max_retries):
            time.sleep(2)  # Wait for processing
            if self.verify_user_creation(player_id):
                return player_id
            logger.info(f"User creation not verified yet, attempt {attempt + 1}/{max_retries}")

        return None

    def publish_game_event(self, player1_id: str, player2_id: str, max_retries=3) -> Optional[str]:
        """Publish a test game event"""
        match_id = str(uuid.uuid4())
        start_time = datetime.now() - timedelta(minutes=5)
        end_time = datetime.now()

        game_event = {
            "eventHeader": {
                "eventID": str(uuid.uuid4()),
                "eventType": "GAME_OVER_STATISTICS_EVENT"
            },
            "eventBody": json.dumps({
                "matchId": match_id,
                "game": "battleship",
                "player1Id": player1_id,
                "player2Id": player2_id,
                "startTime": start_time.isoformat(),
                "endTime": end_time.isoformat(),
                "player1MoveCounts": 10,
                "player2MoveCounts": 9,
                "winnerId": player1_id  # player1 wins
            })
        }

        self.channel.basic_publish(
            exchange='data_analytics_exchange',
            routing_key='game.completed',
            body=json.dumps(game_event)
        )
        logger.info(f"Published game event: {match_id}")

        # Wait and verify with retries
        for attempt in range(max_retries):
            time.sleep(2)  # Wait for processing
            if self.verify_game_record(match_id):
                return match_id
            logger.info(f"Game record not verified yet, attempt {attempt + 1}/{max_retries}")

        return None

    def verify_user_creation(self, user_id: str) -> bool:
        """Verify that the user was created in the database"""
        try:
            # Close and reopen connection to ensure fresh state
            self.db.close()
            self.db = mysql.connector.connect(
                host="localhost",
                port=3309,
                user="root",
                password="root",
                database="platform_analytics"
            )
            self.cursor = self.db.cursor(buffered=True)

            query = """
            SELECT BIN_TO_UUID(player_id) as player_id, username 
            FROM players 
            WHERE player_id = UUID_TO_BIN(%s)
            """
            logger.info(f"Executing verification query for user_id: {user_id}")
            self.cursor.execute(query, (user_id,))
            result = self.cursor.fetchone()

            if result:
                logger.info(f"Found user in database: {result}")
                success = True
            else:
                # Let's check if we can find any users at all
                self.cursor.execute("SELECT COUNT(*) FROM players")
                count = self.cursor.fetchone()[0]
                logger.info(f"Total users in database: {count}")

                # Let's see the most recent users
                self.cursor.execute("""
                    SELECT BIN_TO_UUID(player_id) as player_id, username 
                    FROM players 
                    ORDER BY created_at DESC 
                    LIMIT 3
                """)
                recent_users = self.cursor.fetchall()
                logger.info(f"Most recent users: {recent_users}")
                success = False

            if success:
                logger.info("✓ User creation verified")
            else:
                logger.info("✗ User creation not verified yet")
            return success

        except Exception as e:
            logger.error(f"Error verifying user creation: {str(e)}")
            return False

    def verify_game_record(self, match_id: str) -> bool:
        """Verify that the game record was created in the database"""
        try:
            # Close and reopen connection to ensure fresh state
            self.db.close()
            self.db = mysql.connector.connect(
                host="localhost",
                port=3309,
                user="root",
                password="root",
                database="platform_analytics"
            )
            self.cursor = self.db.cursor(buffered=True)

            # Check match_history
            query = """
            SELECT 
                BIN_TO_UUID(match_id) as match_id,
                BIN_TO_UUID(player1_id) as player1_id,
                BIN_TO_UUID(player2_id) as player2_id,
                BIN_TO_UUID(winner_id) as winner_id,
                start_time,
                end_time,
                result
            FROM match_history 
            WHERE match_id = UUID_TO_BIN(%s)
            """
            self.cursor.execute(query, (match_id,))
            result = self.cursor.fetchone()

            if result:
                logger.info(f"Found game record: {result}")
                success = True
            else:
                # Check recent games
                self.cursor.execute("""
                    SELECT 
                        BIN_TO_UUID(match_id) as match_id,
                        BIN_TO_UUID(player1_id) as player1_id,
                        BIN_TO_UUID(player2_id) as player2_id,
                        result
                    FROM match_history 
                    ORDER BY start_time DESC 
                    LIMIT 3
                """)
                recent_games = self.cursor.fetchall()
                logger.info(f"Most recent games: {recent_games}")
                success = False

            if success:
                logger.info("✓ Game record verified")
            else:
                logger.info("✗ Game record not verified yet")
            return success

        except Exception as e:
            logger.error(f"Error verifying game record: {str(e)}")
            return False

    def verify_player_stats(self, player_id: str) -> bool:
        """Verify that player stats were updated"""
        try:
            query = """
            SELECT total_games_played, total_wins 
            FROM player_game_stats 
            WHERE player_id = UUID_TO_BIN(%s)
            """
            self.cursor.execute(query, (player_id,))
            result = self.cursor.fetchone()
            success = result is not None
            if success:
                logger.info("✓ Player stats verified")
            else:
                logger.info("✗ Player stats not verified yet")
            return success
        except Exception as e:
            logger.error(f"Error verifying player stats: {str(e)}")
            return False

    def run_test_scenario(self):
        """Run a complete test scenario"""
        try:
            logger.info("Starting test scenario...")

            # 1. Ensure test game exists
            game_id = self.ensure_game_exists()
            if not game_id:
                raise Exception("Failed to ensure game exists")

            # 2. Create two test players
            logger.info("\nStep 1: Creating test players...")
            player1_id = self.create_test_player("player1")
            if not player1_id:
                raise Exception("Failed to create player1")

            player2_id = self.create_test_player("player2")
            if not player2_id:
                raise Exception("Failed to create player2")

            # 3. Publish game event
            logger.info("\nStep 2: Publishing game event...")
            match_id = self.publish_game_event(player1_id, player2_id)
            if not match_id:
                raise Exception("Failed to create game record")

            # 4. Verify player stats
            for attempt in range(3):
                time.sleep(1)
                stats1 = self.verify_player_stats(player1_id)
                stats2 = self.verify_player_stats(player2_id)
                if stats1 and stats2:
                    break
                logger.info(f"Player stats not verified yet, attempt {attempt + 1}/3")

            logger.info("\nTest scenario completed successfully!")

        except Exception as e:
            logger.error(f"Error during testing: {str(e)}")
        finally:
            self.connection.close()
            self.db.close()


def main():
    publisher = TestEventPublisher()
    publisher.run_test_scenario()


if __name__ == "__main__":
    main()