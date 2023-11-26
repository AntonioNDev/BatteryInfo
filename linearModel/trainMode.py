import sqlite3
import numpy as np
from sklearn.linear_model import LinearRegression
import joblib
import matplotlib.pyplot as plt

# Connect to the database
conn = sqlite3.connect('../database.db')
cur = conn.cursor()

X = []  # Features (battery percentage differences)
Y = []  # Target (battery percentage change for future time interval)

# Define the time intervals for prediction (e.g., 30 minutes)
prediction_interval = 2
months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct']

# Iterate over the database data and calculate differences
for month in months:
    cur.execute(f"SELECT time, batteryPerc FROM {month};")
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
joblib.dump(model, 'linear_regression_model.pkl')

# Load the saved model
loaded_model = joblib.load('linear_regression_model.pkl')

# Now, you can use the trained model to make predictions
# Let's test it with a sample input (battery percentage differences)
sample_input = X[-1]  # Use the first set of battery percentage differences from the data
print(X, sample_input)

# Predict the battery percentage change
predicted_change = loaded_model.predict([sample_input])

# Get the actual battery percentage data for a specific day in September
cur.execute("SELECT time, batteryPerc FROM Oct WHERE day='Mon 16';")
actual_data = cur.fetchall()
actual_data = np.array(actual_data)

# Create timestamps for plotting
timestamps = [f"{t} mins" for t in range(len(actual_data))]

# Extend the x-axis for future predictions
future_timestamps = [f"{t} mins" for t in range(len(actual_data), len(actual_data) + len(predicted_change))]

# Create a figure and axis for the plot
plt.figure(figsize=(10, 6))

# Plot the actual data
plt.plot(timestamps, actual_data[:, 1], label='Actual Data', marker='o', linestyle='-')

# Extend the plot for predicted data in the future
last_actual_point = actual_data[-1, 1]
predicted_future_data = [last_actual_point + np.sum(predicted_change[:i+1]) for i in range(len(predicted_change))]
plt.plot(future_timestamps, predicted_future_data, label='Predicted Data (Future)', marker='x', linestyle='--')

# Set labels and title
plt.xlabel("Time")
plt.ylabel("Battery Percentage")
plt.title("Actual vs. Predicted Battery Percentage")

# Add a legend
plt.legend()

# Show the plot
plt.tight_layout()
plt.xticks(rotation=45)
plt.grid(True)
plt.show()
