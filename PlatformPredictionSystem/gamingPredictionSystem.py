import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_squared_error, classification_report
import matplotlib.pyplot as plt
import seaborn as sns


class GamingPredictionSystem:
    def __init__(self, csv_path):
        """
        Initialize prediction system with CSV data

        Args:
            csv_path (str): Path to the CSV file containing player data
        """
        self.data = pd.read_csv(csv_path)
        self.prepare_data()

    def prepare_data(self):
        """
        Clean and prepare the data for analysis
        """
        # Handle missing values
        self.data = self.data.dropna()

        # Calculate derived features
        self.data['moves_per_game'] = self.data['total_moves'] / self.data['total_games_played']
        self.data['avg_game_duration'] = self.data['total_time_played_minutes'] / self.data['total_games_played']
        self.data['win_ratio'] = self.data['wins'] / self.data['total_games_played']

        # Define churn (players with less than 5 games in last 30 days)
        self.data['is_churned'] = (self.data['total_games_played'] < 5).astype(int)

    def prepare_features(self):
        """
        Prepare features for model training

        Returns:
            tuple: Prepared features and target variables
        """
        # Select numerical features
        numerical_features = [
            'age',
            'total_games_played',
            'total_moves',
            'moves_per_game',
            'total_time_played_minutes',
            'avg_game_duration'
        ]

        # One-hot encode categorical variables
        categorical_features = ['gender', 'location']
        data_encoded = pd.get_dummies(self.data, columns=categorical_features)

        # Combine features
        feature_columns = numerical_features + [col for col in data_encoded.columns
                                                if col.startswith(('gender_', 'location_'))]
        X = data_encoded[feature_columns]

        # Define target variables
        y_churn = data_encoded['is_churned']
        y_win_ratio = data_encoded['win_ratio']

        return X, y_churn, y_win_ratio

    def predict_player_churn(self):
        """
        Predict player churn probability

        Returns:
            dict: Churn prediction model metrics and visualization
        """
        X, y_churn, _ = self.prepare_features()

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y_churn, test_size=0.2, random_state=42)

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Train model
        churn_model = RandomForestClassifier(n_estimators=100, random_state=42)
        churn_model.fit(X_train_scaled, y_train)

        # Make predictions
        y_pred = churn_model.predict(X_test_scaled)
        y_prob = churn_model.predict_proba(X_test_scaled)[:, 1]

        # Get feature importance
        feature_importance = dict(zip(X.columns, churn_model.feature_importances_))
        top_features = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5])

        return {
            'accuracy': accuracy_score(y_test, y_pred),
            'classification_report': classification_report(y_test, y_pred),
            'feature_importance': top_features,
            'churn_probabilities': y_prob
        }

    def predict_win_probability(self):
        """
        Predict win probability for players

        Returns:
            dict: Win probability prediction metrics and visualization
        """
        X, _, y_win_ratio = self.prepare_features()

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y_win_ratio, test_size=0.2, random_state=42)

        # Train model
        win_model = RandomForestRegressor(n_estimators=100, random_state=42)
        win_model.fit(X_train, y_train)

        # Make predictions
        y_pred = win_model.predict(X_test)

        # Get feature importance
        feature_importance = dict(zip(X.columns, win_model.feature_importances_))
        top_features = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5])

        return {
            'mse': mean_squared_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'feature_importance': top_features,
            'predicted_win_ratios': y_pred
        }

    def generate_player_insights(self):
        """
        Generate comprehensive player insights and visualizations

        Returns:
            dict: Player performance insights and statistics
        """
        insights = {
            'player_demographics': {
                'age_distribution': self.data['age'].describe(),
                'gender_distribution': self.data['gender'].value_counts(),
                'location_distribution': self.data['location'].value_counts()
            },
            'game_statistics': {
                'avg_games_per_player': self.data['total_games_played'].mean(),
                'avg_win_ratio': self.data['win_ratio'].mean(),
                'avg_time_per_game': self.data['avg_game_duration'].mean()
            },
            'performance_metrics': {
                'top_players': self.data.nlargest(10, 'win_ratio')[['player_id', 'win_ratio', 'total_games_played']],
                'most_active': self.data.nlargest(10, 'total_games_played')[
                    ['player_id', 'total_games_played', 'win_ratio']]
            }
        }
        return insights


def main():
    # Initialize prediction system
    predictor = GamingPredictionSystem('../Battleship/battleship_player_data.csv')

    # Generate churn predictions
    print("\nPlayer Churn Prediction Results:")
    churn_results = predictor.predict_player_churn()
    print(f"Model Accuracy: {churn_results['accuracy']:.2f}")
    print("\nClassification Report:")
    print(churn_results['classification_report'])
    print("\nTop Features for Churn Prediction:")
    for feature, importance in churn_results['feature_importance'].items():
        print(f"{feature}: {importance:.4f}")

    # Generate win probability predictions
    print("\nWin Probability Prediction Results:")
    win_results = predictor.predict_win_probability()
    print(f"Root Mean Square Error: {win_results['rmse']:.4f}")
    print("\nTop Features for Win Prediction:")
    for feature, importance in win_results['feature_importance'].items():
        print(f"{feature}: {importance:.4f}")


if __name__ == "__main__":
    main()