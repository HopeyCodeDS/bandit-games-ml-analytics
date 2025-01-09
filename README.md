# Data Analytics Microservice

This repository contains a MySQL database, event listener via rabbitMQ, Statistics API and Prediction API for statistics, analytics and prediction services needed in the Platform frontend.

## Features

- Comprehensive Player and Game Data System
- RabbitMQ listener that listens to user and game events from the Core and Game Platforms and store the data to the Analytics Database
- Prediction Model (Player Churn, Win Probability, Player Classification and Player Game Engagement) development
- Machine learning APIs using FastAPI 
- Docker containerization of all services for easy deployment
- Azure App Service integration for hosting

## Tech Stack

- Python 3.9
- FastAPI
- Jupyter notebook
- Machine learning algorithms
- Docker
- Azure App Service
- GitLab CI/CD

## Usage

**To use the services, you just need to**:
```bash
# Pull the images
docker pull opeyemimomodu/statistics-api:latest
docker pull opeyemimomodu/prediction-api:latest
docker pull opeyemimomodu/analytics-consumer:latest
docker pull mysql:latest

OR

# Clone the repository
git clone https://gitlab.com/kdg-ti/integration-5/2024-2025/team7/analytics.git

# Branch creation
git checkout <feature-branch>

# Navigate to the root directory
cd analytics

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the services
docker-compose up -d

# Deploy
- Commit and Push
- The .gitlab-ci.yml file is triggerred. In has 4 stages (build, migrate, test and deploy)
- The services are deployed to Azure Cloud to be used by other platforms.

