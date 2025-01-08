import mysql.connector
import os

def check_database():
    # Use the same connection details as your consumer
    config = {
        "host": os.getenv('DB_HOST'),
        "port": int(os.getenv('DB_PORT', '3306')),
        "user": os.getenv('DB_USER'),
        "password": os.getenv('DB_PASSWORD'),
        "database": os.getenv('DB_NAME'),
        "ssl_ca": "/etc/ssl/certs/ca-certificates.crt"
    }

    conn = mysql.connector.connect(**config)
    cursor = conn.cursor(dictionary=True)

    # Check recent matches
    print("\nChecking recent matches:")
    cursor.execute("""
        SELECT BIN_TO_UUID(match_id) as match_id, 
               BIN_TO_UUID(player1_id) as player1_id,
               BIN_TO_UUID(player2_id) as player2_id,
               start_time, end_time
        FROM match_history
        ORDER BY start_time DESC
        LIMIT 5
    """)
    matches = cursor.fetchall()
    for match in matches:
        print(match)

    # Check recent players
    print("\nChecking recent players:")
    cursor.execute("""
        SELECT BIN_TO_UUID(player_id) as player_id,
               username, email, created_at
        FROM players
        ORDER BY created_at DESC
        LIMIT 5
    """)
    players = cursor.fetchall()
    for player in players:
        print(player)

    conn.close()

if __name__ == "__main__":
    check_database()