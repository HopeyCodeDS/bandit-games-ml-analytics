import requests
import uuid
import sys
from requests.exceptions import RequestException

# API base URL
BASE_URL = "http://localhost:8000"


def print_response(endpoint, response):
    print(f"\nTesting: {endpoint}")
    print(f"Status Code: {response.status_code}")
    try:
        print("Response:", response.json())
    except ValueError:
        print("Response: Could not parse JSON response")
    print("-" * 50)


def test_api_manually():
    try:
        # Test root endpoint
        print("\n1. Testing root endpoint...")
        try:
            response = requests.get(f"{BASE_URL}/")
            print_response("/", response)
        except RequestException as e:
            print(f"Error accessing root endpoint: {e}")
            print("Is the API server running on {BASE_URL}?")
            sys.exit(1)

        # Test get all player stats
        print("\n2. Testing get all player stats...")
        try:
            response = requests.get(f"{BASE_URL}/players/stats")
            print_response("/players/stats", response)

            if response.status_code == 200:
                players = response.json()
                print(f"Found {len(players)} players")
                if players:
                    print("\nFirst player data:")
                    for key, value in players[0].items():
                        print(f"{key}: {value}")
            elif response.status_code == 500:
                print("Database connection error. Check your database connection settings.")

        except RequestException as e:
            print(f"Error getting player stats: {e}")

        # Test get all game stats
        print("\n3. Testing get all game stats...")
        try:
            response = requests.get(f"{BASE_URL}/games/stats")
            print_response("/games/stats", response)

            if response.status_code == 200:
                games = response.json()
                print(f"Found {len(games)} games")
                if games:
                    print("\nFirst game data:")
                    for key, value in games[0].items():
                        print(f"{key}: {value}")

                    # Test specific game
                    game_name = games[0]['game_name']
                    print(f"\n4. Testing specific game: {game_name}")
                    game_response = requests.get(f"{BASE_URL}/game/{game_name}/stats")
                    print_response(f"/game/{game_name}/stats", game_response)
            elif response.status_code == 500:
                print("Database connection error. Check your database connection settings.")

        except RequestException as e:
            print(f"Error getting game stats: {e}")

        # Test error cases
        print("\n5. Testing invalid player ID...")
        invalid_id = uuid.uuid4()
        try:
            response = requests.get(f"{BASE_URL}/player/{invalid_id}/stats")
            print_response(f"/player/{invalid_id}/stats", response)
        except RequestException as e:
            print(f"Error testing invalid player ID: {e}")

        print("\n6. Testing invalid game name...")
        try:
            response = requests.get(f"{BASE_URL}/game/nonexistent_game/stats")
            print_response("/game/nonexistent_game/stats", response)
        except RequestException as e:
            print(f"Error testing invalid game: {e}")

    except Exception as e:
        print(f"\nUnexpected error occurred: {e}")
    finally:
        print("\nTest script completed.")


def check_server():
    """Check if the API server is running"""
    try:
        requests.get(BASE_URL)
        return True
    except RequestException:
        return False


if __name__ == "__main__":
    print("Game Analytics API Manual Test Script")
    print(f"API URL: {BASE_URL}")

    if not check_server():
        print("\nERROR: Could not connect to the API server!")
        print("Please ensure that:")
        print("1. The API server is running (use 'uvicorn main:app --reload')")
        print("2. The server is running on", BASE_URL)
        print("3. There are no firewall issues blocking the connection")
        sys.exit(1)

    test_api_manually()