import sqlite3
import numpy as np
from sklearn.linear_model import LinearRegression
import joblib
import matplotlib.pyplot as plt
import datetime

# Connect to the database
conn = sqlite3.connect('C:/Users/Antonio/Documents/MyProjects/BatteryInfo/database.db')
cur = conn.cursor()

X = []  # Features (battery percentage differences)
Y = []  # Target (battery percentage change for future time interval)

# Define the time intervals for prediction (e.g., 30 minutes)
prediction_interval = 2
months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
years = [2023, 2024]

now = datetime.datetime.now()

day = now.strftime("%a %d")
month = now.strftime("%b")

# Iterate over the database data and calculate differences
for month in months:
    for year in years:
        cur.execute(f"SELECT time, batteryPerc FROM {month} WHERE year='{year}';")
        data = cur.fetchall()
        data = np.array(data)
        
        # Calculate battery percentage differences for the chosen interval
        for i in range(len(data) - prediction_interval):
            features = data[i:i+prediction_interval, 1]  # Battery percentage values
            target = data[i+prediction_interval, 1] - data[i, 1]  # Battery percentage change over the interval
            
            # Exclude differences greater than or equal to 10%
            if abs(target) < 10:
                X.append(features)
                Y.append(target)

# Find the maximum length among X and Y
max_length = max(len(X), len(Y))

# Pad X and Y with zeros to make them the same length
X = np.pad(X, ((0, max_length - len(X)), (0, 0)), mode='constant')
Y = np.pad(Y, (0, max_length - len(Y)), mode='constant')

# Convert lists to numpy arrays
X = np.array(X)
Y = np.array(Y)

# Create and train the Linear Regression model
model = LinearRegression()
model.fit(X, Y)

# Save the trained model to a file
joblib.dump(model, 'C:/Users/Antonio/Documents/MyProjects/BatteryInfo/linearModel/linear_regression_model2024.pkl')

# Load the saved model
loaded_model = joblib.load('C:/Users/Antonio/Documents/MyProjects/BatteryInfo/linearModel/linear_regression_model2024.pkl')
print("Model trained.")
