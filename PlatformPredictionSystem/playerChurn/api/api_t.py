import requests
from datetime import datetime

# Define the API endpoint
url = "http://localhost:8000/predict/churn"  # Updated port to 8000 and correct endpoint

# Example test payload matching the PlayerData model
test_data = {
    "total_time_played_minutes": 600,  # Added required field
    "total_games_played": 120,
    "total_wins": 80,
    "total_moves": 5000,
    "age": 25,
    "last_played": datetime.now().isoformat()  # Added required field
}

try:
    # Send POST request to the API
    response = requests.post(url, json=test_data)

    # Print the response
    if response.status_code == 200:
        print("Prediction successful!")
        print("\nPrediction Response:")
        prediction = response.json()
        print(f"Churn Probability: {prediction['churn_probability']:.2%}")
        print(f"Prediction Time: {prediction['prediction_timestamp']}")
        print("\nFeatures Used:")
        for feature, value in prediction['features_used'].items():
            print(f"{feature}: {value}")
    else:
        print(f"Request failed with status code {response.status_code}")
        print("Error message:", response.text)

except requests.exceptions.ConnectionError:
    print("Connection Error: Make sure the API server is running at", url)
except Exception as e:
    print("Error occurred:", str(e))