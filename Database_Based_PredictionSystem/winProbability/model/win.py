import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report
import pickle

# Step 1: Load and prepare data
print("Step 1: Loading data...")
df = pd.read_csv('../../data/player_game_statistics.csv')

# Step 2: Basic feature engineering
print("Step 2: Creating basic features...")
df['avg_session_duration'] = df['total_time_played_minutes'] / df['total_games_played']
df['historical_win_rate'] = df['total_wins'] / df['total_games_played']
df['avg_moves_per_game'] = df['total_moves'] / df['total_games_played']

# Step 3: Encode game names into numbers
print("Step 3: Encoding game names...")
game_encoder = LabelEncoder()
df['game_encoded'] = game_encoder.fit_transform(df['game_name'])

# Step 4: Calculate win rate per game type
print("Step 4: Calculating game-specific win rates...")
game_win_rates = df.groupby('game_name')['historical_win_rate'].mean().reset_index()
game_win_rates.columns = ['game_name', 'game_avg_win_rate']
df = df.merge(game_win_rates, on='game_name')

# Step 5: Select features for model
print("Step 5: Preparing features for model...")
features = [
    'avg_session_duration',
    'historical_win_rate',
    'avg_moves_per_game',
    'game_encoded',
    'game_avg_win_rate',
    'age'
]

X = df[features]

# Step 6: Create target variable (win or lose)
print("Step 6: Creating target variable...")
df['next_game_win'] = (df['historical_win_rate'] > df['historical_win_rate'].mean()).astype(int)
y = df['next_game_win']

# Step 7: Split data into train and test sets
print("Step 7: Splitting data...")
# Split by player_id to keep all data for the same player together
unique_players = df['player_id'].unique()
train_players, test_players = train_test_split(unique_players, test_size=0.2, random_state=42)

train_mask = df['player_id'].isin(train_players)
test_mask = df['player_id'].isin(test_players)

X_train = X[train_mask]
X_test = X[test_mask]
y_train = y[train_mask]
y_test = y[test_mask]

# Step 8: Scale the features
print("Step 8: Scaling features...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Step 9: Train the model
print("Step 9: Training model...")
model = GradientBoostingClassifier(n_estimators=100, random_state=42)
model.fit(X_train_scaled, y_train)

# Step 10: Evaluate the model
print("Step 10: Evaluating model...")
y_pred = model.predict(X_test_scaled)
print("\nModel Performance:")
print(classification_report(y_test, y_pred))

# Step 11: Show feature importance
print("\nFeature Importance:")
importance_df = pd.DataFrame({
    'feature': features,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)
print(importance_df)

# Step 12: Save the model and necessary components
print("\nStep 12: Saving model and components...")
with open('win_probability_model.pkl', 'wb') as f:
    pickle.dump(model, f)
with open('win_probability_scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)
with open('game_encoder.pkl', 'wb') as f:
    pickle.dump(game_encoder, f)

print("\nTraining complete! Model and components saved.")