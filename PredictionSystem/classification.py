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

# Load the data
df = pd.read_csv('player_game_statistics_old.csv')

# Prepare features
le_gender = LabelEncoder()
le_country = LabelEncoder()
df['gender_encoded'] = le_gender.fit_transform(df['gender'])
df['country_encoded'] = le_country.fit_transform(df['country'])


# Create player classes based on rating and win ratio
def assign_player_class(row):
    if row['rating'] >= 4 and row['win_ratio'] >= 60:
        return 'expert'
    elif row['rating'] >= 3 and row['win_ratio'] >= 45:
        return 'intermediate'
    else:
        return 'novice'


df['player_class'] = df.apply(assign_player_class, axis=1)

# Encode player class
le_class = LabelEncoder()
df['player_class_encoded'] = le_class.fit_transform(df['player_class'])

# Select features
features = [
    'total_games_played',
    'total_wins',
    'total_losses',
    'total_moves',
    'total_time_played_minutes',
    'win_ratio',
    'age',
    'gender_encoded',
    'country_encoded'
]

X = df[features]
y = df['player_class_encoded']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Initialize models
models = {
    'Random Forest': RandomForestClassifier(random_state=42),
    'Logistic Regression': LogisticRegression(random_state=42, multi_class='multinomial'),
    'XGBoost': XGBClassifier(random_state=42),
    'SVM': SVC(random_state=42)
}

# Dictionary to store model performances
model_performances = {}

# Train and evaluate models
for name, model in models.items():
    print(f"\nTraining {name}...")
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)

    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=le_class.classes_, output_dict=True)

    model_performances[name] = {
        'model': model,
        'accuracy': accuracy,
        'report': report
    }

    print(f"\nResults for {name}:")
    print(f"Accuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=le_class.classes_))

# Select the best model based on accuracy
best_model_name = max(model_performances.items(), key=lambda x: x[1]['accuracy'])[0]
best_model = model_performances[best_model_name]['model']

print(f"\nBest performing model: {best_model_name}")
print(f"Best Accuracy: {model_performances[best_model_name]['accuracy']:.4f}")
print("\nDetailed Classification Report for Best Model:")
print(classification_report(y_test, best_model.predict(X_test_scaled), target_names=le_class.classes_))

# Save best model, scaler, and label encoders
with open('classification_model.pkl', 'wb') as f:
    pickle.dump(best_model, f)

with open('classification_scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

with open('classification_label_encoder.pkl', 'wb') as f:
    pickle.dump(le_class, f)

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
    for class_idx, class_name in enumerate(le_class.classes_):
        print(f"\nCoefficients for class {class_name}:")
        for feat, coef in zip(features, best_model.coef_[class_idx]):
            print(f"{feat}: {coef:.4f}")

# Create test data example
test_data = {
    'total_games_played': 100,
    'total_wins': 55,
    'total_losses': 45,
    'total_moves': 2000,
    'total_time_played_minutes': 3000,
    'win_ratio': 55.0,
    'age': 25,
    'gender_encoded': 1,
    'country_encoded': 0
}

print("\nExample prediction with test data:")
test_df = pd.DataFrame([test_data])
test_scaled = scaler.transform(test_df)
prediction = best_model.predict(test_scaled)
predicted_class = le_class.inverse_transform(prediction)[0]
print(f"Predicted player class: {predicted_class}")

# If the model supports probability predictions, show them
if hasattr(best_model, 'predict_proba'):
    probabilities = best_model.predict_proba(test_scaled)[0]
    print("\nClass probabilities:")
    for class_name, prob in zip(le_class.classes_, probabilities):
        print(f"{class_name}: {prob:.2%}")