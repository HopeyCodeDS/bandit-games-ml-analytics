from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
import pandas as pd
from joblib import load
from fastapi.middleware.cors import CORSMiddleware

# Load the trained model, scaler, and encoded column structure
model = load('../model/xgb_model.joblib')
scaler = load('../model/scaler.joblib')
encoded_columns = np.load('../model/encoded_columns.npy', allow_pickle=True)

# Convert encoded_columns to list of strings if they aren't already
encoded_columns = [str(col) for col in encoded_columns]

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PlayerData(BaseModel):
    age: int
    gender: int
    total_games_played: int
    total_wins: int
    total_losses: int
    win_ratio: float
    total_moves: float
    highest_score: int
    rating: int
    country: str
    game_name: str


@app.get("/")
def root():
    return {"message": "Welcome to the ML Model API for Player Churn Prediction!"}


@app.post("/predict/")
def predict(data: PlayerData):
    try:
        # Convert incoming data to a dictionary
        input_dict = data.dict()

        # Create initial DataFrame
        input_df = pd.DataFrame([input_dict])

        # Debug print
        print("Initial DataFrame columns:", input_df.columns.tolist())
        print("Initial DataFrame shape:", input_df.shape)

        # Perform one-hot encoding
        input_df = pd.get_dummies(input_df, columns=['country', 'game_name'])

        # Debug print
        print("After one-hot encoding columns:", input_df.columns.tolist())
        print("After one-hot encoding shape:", input_df.shape)
        print("Expected encoded columns:", encoded_columns)

        # Create a DataFrame with all expected columns initialized to 0
        final_df = pd.DataFrame(0, index=input_df.index, columns=encoded_columns)

        # Copy values from input_df to final_df for columns that exist
        for col in input_df.columns:
            if col in encoded_columns:
                final_df[col] = input_df[col]

        # Debug print
        print("Final DataFrame columns:", final_df.columns.tolist())
        print("Final DataFrame shape:", final_df.shape)
        print("Scaler expected features:", scaler.feature_names_in_.tolist())

        # Ensure column order matches scaler's expected order
        final_df = final_df[scaler.feature_names_in_]

        # Scale the features
        scaled_data = scaler.transform(final_df)

        # Make prediction
        prediction = model.predict(scaled_data)

        return {
            "prediction": "Churn" if prediction[0] == 1 else "No Churn",
            "status": "success",
            "debug_info": {
                "input_columns": input_df.columns.tolist(),
                "final_columns": final_df.columns.tolist(),
                "expected_columns": encoded_columns
            }
        }

    except Exception as e:
        print(f"Error details: {str(e)}")  # This will show in your server logs
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Prediction error",
                "message": str(e),
                "type": str(type(e).__name__)
            }
        )