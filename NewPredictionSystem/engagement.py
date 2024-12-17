import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from xgboost import XGBRegressor
from sklearn.svm import SVR
import pickle

# Load the data
df = pd.read_csv('player_game_statistics.csv')

# Prepare features
le_gender = LabelEncoder()
le_country = LabelEncoder()
df['gender_encoded'] = le_gender.fit_transform(df['gender'])
df['country_encoded'] = le_country.fit_transform(df['country'])

# Target variable: average time per game
df['avg_engagement_time'] = df['total_time_played_minutes'] / df['total_games_played']

# Select features
features = [
    'total_games_played',
    'total_wins',
    'total_losses',
    'total_moves',
    'win_ratio',
    'rating',
    'age',
    'gender_encoded',
    'country_encoded'
]

X = df[features]
y = df['avg_engagement_time']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Initialize models
models = {
    'Random Forest': RandomForestRegressor(random_state=42),
    'Linear Regression': LinearRegression(),
    'XGBoost': XGBRegressor(random_state=42),
    'SVR': SVR(kernel='rbf')
}

# Dictionary to store model performances
model_performances = {}

# Train and evaluate models
for name, model in models.items():
    print(f"\nTraining {name}...")
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)

    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    model_performances[name] = {
        'model': model,
        'mse': mse,
        'r2': r2
    }

    print(f"\nResults for {name}:")
    print(f"Mean Squared Error: {mse:.4f}")
    print(f"R2 Score: {r2:.4f}")

# Select the best model based on R2 score
best_model_name = max(model_performances.items(), key=lambda x: x[1]['r2'])[0]
best_model = model_performances[best_model_name]['model']

print(f"\nBest performing model: {best_model_name}")
print(f"Best R2 Score: {model_performances[best_model_name]['r2']:.4f}")
print(f"Best MSE: {model_performances[best_model_name]['mse']:.4f}")

# Save best model and scaler
with open('engagement_model.pkl', 'wb') as f:
    pickle.dump(best_model, f)

with open('engagement_scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

# Print feature importances if the best model supports it
if hasattr(best_model, 'feature_importances_'):
    print("\nFeature importances:")
    for feat, imp in zip(features, best_model.feature_importances_):
        print(f"{feat}: {imp:.4f}")
elif hasattr(best_model, 'coef_'):
    print("\nFeature coefficients:")
    for feat, coef in zip(features, best_model.coef_):
        print(f"{feat}: {coef:.4f}")

# Create test data example
test_data = {
    'total_games_played': 100,
    'total_wins': 55,
    'total_losses': 45,
    'total_moves': 2000,
    'win_ratio': 55.0,
    'rating': 4,
    'age': 25,
    'gender_encoded': 1,
    'country_encoded': 0
}

print("\nExample prediction with test data:")
test_df = pd.DataFrame([test_data])
test_scaled = scaler.transform(test_df)
prediction = best_model.predict(test_scaled)
print(f"Predicted engagement time per game: {prediction[0]:.2f} minutes")