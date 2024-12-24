import pickle
import pandas as pd


def load_churn_model():
    """Load the saved churn prediction model and preprocessing objects"""
    with open('../models/best_churn_model.pkl', 'rb') as f:
        model = pickle.load(f)

    with open('../models/churn_scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)

    with open('../models/encoders.pkl', 'rb') as f:
        encoders = pickle.load(f)

    return model, scaler, encoders


def predict_churn(data):
    """
    Predict churn based on simple rules:
    - Churned (1) if games < 10 OR win_ratio < 0.2
    - Not churned (0) otherwise
    """
    predictions = (data['total_games_played'] < 10) | (data['win_ratio'] < 0.2)
    return predictions.astype(int)


# Create test data with clear churn/not churn cases
test_data = pd.DataFrame({
    'total_games_played': [5, 1500, 3, 800, 10, 2000],  # Very low vs very high
    'win_ratio': [0.1, 0.85, 0.05, 0.75, 0.15, 0.90],  # Very poor vs excellent
    'total_time_played_minutes': [50, 20000, 30, 15000, 100, 25000],  # Minimal vs heavy
    'gender': ['Male', 'Female', 'Male', 'Female', 'Male', 'Female'],
    'country': ['USA', 'UK', 'South Korea', 'USA', 'UK', 'Japan'],
    'age': [25, 31, 19, 28, 22, 35]
})

# Make predictions
predictions = predict_churn(test_data)

# Print results with more context
for i, pred in enumerate(predictions):
    print(f"\nPlayer {i + 1}:")
    print(f"Games Played: {test_data['total_games_played'][i]}")
    print(f"Win Ratio: {test_data['win_ratio'][i]:.2f}")
    print(f"Time Played: {test_data['total_time_played_minutes'][i]} minutes")
    print(f"Gender: {test_data['gender'][i]}")
    print(f"Country: {test_data['country'][i]}")
    print(f"Age: {test_data['age'][i]}")
    print(f"Risk Factors:")
    if test_data['total_games_played'][i] < 10:
        print("- Low number of games played")
    if test_data['win_ratio'][i] < 0.2:
        print("- Low win ratio")
    print(f"Predicted to Churn: {'Yes' if pred else 'No'}")
    print("-" * 30)