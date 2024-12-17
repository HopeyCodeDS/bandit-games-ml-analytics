import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.svm import SVC
import pickle

# Load data
df = pd.read_csv('player_game_statistics.csv')

# Simple feature preparation
# Encode categorical variables
le_gender = LabelEncoder()
le_country = LabelEncoder()
df['gender_encoded'] = le_gender.fit_transform(df['gender'])
df['country_encoded'] = le_gender.fit_transform(df['country'])

# Convert last_played to datetime and calculate days since last played
df['last_played'] = pd.to_datetime(df['last_played'])
df['days_since_last_play'] = (pd.Timestamp.now() - df['last_played']).dt.days

# Define churn (player is considered churned if they haven't played in 30 days and have below average win ratio)
avg_win_ratio = df['win_ratio'].mean()
df['churned'] = ((df['days_since_last_play'] > 30) & (df['win_ratio'] < avg_win_ratio)).astype(int)

# Select features
features = [
    'total_games_played',
    'total_wins',
    'total_losses',
    'total_moves',
    'total_time_played_minutes',
    'win_ratio',
    'rating',
    'age',
    'gender_encoded',
    'country_encoded',
    'days_since_last_play'
]

X = df[features]
y = df['churned']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Initialize models
models = {
    'Random Forest': RandomForestClassifier(random_state=42),
    'Logistic Regression': LogisticRegression(random_state=42),
    'XGBoost': XGBClassifier(random_state=42),
    'SVM': SVC(random_state=42, probability=True)  # Enable probability estimates for SVM
}

# Dictionary to store model performances
model_performances = {}

# Train and evaluate models
for name, model in models.items():
    print(f"\nTraining {name}...")
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)

    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)

    model_performances[name] = {
        'model': model,
        'accuracy': accuracy,
        'report': report
    }

    print(f"\nResults for {name}:")
    print(f"Accuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

# Select the best model based on accuracy
best_model_name = max(model_performances.items(), key=lambda x: x[1]['accuracy'])[0]
best_model = model_performances[best_model_name]['model']

print(f"\nBest performing model: {best_model_name}")
print(f"Best Accuracy: {model_performances[best_model_name]['accuracy']:.4f}")
print("\nDetailed Classification Report for Best Model:")
print(classification_report(y_test, best_model.predict(X_test_scaled)))

# Save best model, scaler, and encoders
with open('churn_model.pkl', 'wb') as f:
    pickle.dump(best_model, f)

with open('churn_scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

with open('gender_encoder.pkl', 'wb') as f:
    pickle.dump(le_gender, f)

with open('country_encoder.pkl', 'wb') as f:
    pickle.dump(le_country, f)

# Print feature importances if the best model supports it
if hasattr(best_model, 'feature_importances_'):
    print("\nFeature importances:")
    for feat, imp in zip(features, best_model.feature_importances_):
        print(f"{feat}: {imp:.4f}")
elif hasattr(best_model, 'coef_'):
    print("\nFeature coefficients:")
    for feat, coef in zip(features, best_model.coef_[0]):
        print(f"{feat}: {coef:.4f}")

# Create test data example
test_data = {
    "total_games_played": 100,
    "total_wins": 55,
    "total_losses": 45,
    "total_moves": 2000,
    "total_time_played_minutes": 3000,
    "win_ratio": 55.0,
    "rating": 4,
    "age": 25,
    "gender_encoded": 1,
    "country_encoded": 0,
    "days_since_last_play": 15
}

test_data2 = {
    "total_games_played": 20,
    "total_wins": 4,
    "total_losses": 16,
    "total_moves": 500,
    "total_time_played_minutes": 600,
    "win_ratio": 20.0,
    "rating": 2,
    "age": 25,
    "gender_encoded": 1,
    "country_encoded": 0,
    "days_since_last_play": 45
}

print("\nExample prediction with test data:")
test_df = pd.DataFrame([test_data])
test_scaled = scaler.transform(test_df)
prediction = best_model.predict(test_scaled)
print(f"Churn prediction: {'Yes' if prediction[0] == 1 else 'No'}")

# Show probability of churn if model supports it
if hasattr(best_model, 'predict_proba'):
    churn_prob = best_model.predict_proba(test_scaled)[0]
    print(f"Probability of churning: {churn_prob[1]:.2%}")
    print(f"Probability of staying: {churn_prob[0]:.2%}")

# Save threshold values for future reference
thresholds = {
    'avg_win_ratio': avg_win_ratio,
    'churn_days_threshold': 30
}

with open('churn_thresholds.pkl', 'wb') as f:
    pickle.dump(thresholds, f)