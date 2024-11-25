import pandas as pd
import numpy as np
import random
import requests
from faker import Faker


class BattleshipDataGenerator:
    def __init__(self, num_players=1000):
        self.fake = Faker()
        self.num_players = num_players
        self.data = self.generate_player_data()

    def generate_player_data(self):
        """
        Generate realistic Battleship player data
        """
        data = []
        for _ in range(self.num_players):
            total_games = random.randint(1, 100)
            wins = random.randint(0, total_games)

            player = {
                'player_id': self.fake.uuid4(),
                'username': self.fake.user_name(),
                'age': random.randint(18, 65),
                'gender': random.choice(['Male', 'Female', 'Other']),
                'location': self.fake.country(),
                'total_games': total_games,
                'wins': wins,
                'losses': total_games - wins,
                'total_time_played': total_games * random.randint(15, 45),  # minutes
                'total_moves': total_games * random.randint(20, 100),
                'win_ratio': wins / total_games if total_games > 0 else 0
            }
            data.append(player)

        return pd.DataFrame(data)

    def export_to_csv(self, filename='battleship_player_data.csv'):
        """
        Export generated data to CSV
        """
        self.data.to_csv(filename, index=False)
        return filename

    def send_to_api(self, api_url):
        """
        Send generated player data to Spring Boot API
        """
        players_data = self.data.to_dict('records')

        try:
            response = requests.post(
                api_url,
                json=players_data,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API transmission error: {e}")
            return None


def main():
    # Generate Battleship player data
    data_generator = BattleshipDataGenerator(num_players=1200)

    # Export to CSV (optional)
    csv_file = data_generator.export_to_csv()
    print(f"Data exported to {csv_file}")

    # Send to Spring Boot API (endpoint)
    api_url = 'http://localhost:8080/api/players/bulk-import'
    api_response = data_generator.send_to_api(api_url)

    if api_response:
        print("Data successfully sent to API")


if __name__ == "__main__":
    main()