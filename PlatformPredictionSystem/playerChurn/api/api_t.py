import requests

# Define the API endpoint
url = "http://localhost:8080/predict/"  # Adjust if your API runs on a different port or host

# Example test payload
test_data = {
    "age": 25,
    "gender": 1,
    "total_games_played": 120,
    "total_wins": 80,
    "total_losses": 40,
    "win_ratio": 0.67,
    "total_moves": 5000,
    "highest_score": 2000,
    "rating": 1500,
    "country": "USA",
    "game_name": "Battleship"
}

# Send POST request to the API
response = requests.post(url, json=test_data)

# Print the response
if response.status_code == 200:
    print("Prediction Response:", response.json())
else:
    print(f"Failed with status code {response.status_code}: {response.text}")
