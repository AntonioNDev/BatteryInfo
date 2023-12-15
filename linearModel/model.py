import sqlite3
import numpy as np
import joblib
import matplotlib.pyplot as plt
import datetime

# Connect to the database
conn = sqlite3.connect('C:/Users/Antonio/Documents/MyProjects/BatteryInfo/database.db')
cur = conn.cursor()

X = []  # Features (battery percentage differences)
Y = []  # Target (battery percentage change for future time interval)

now = datetime.datetime.now()

day = now.strftime("%a %d")
month = now.strftime("%b")
year = now.strftime("%Y")

# Define the time intervals for prediction (e.g., 3 minutes)
prediction_interval = 2

# Iterate over the database data and calculate differences

cur.execute(f"SELECT time, batteryPerc FROM {month} WHERE day ='{day}';")
data = cur.fetchall()
data = np.array(data)
print(data)
    
# Calculate battery percentage differences for the chosen interval
for i in range(len(data) - prediction_interval):
    features = data[i:i+prediction_interval, 1]  # Battery percentage values
    target = data[i+prediction_interval, 1] - data[i, 1]  # Battery percentage change over the interval

    # Exclude differences greater than or equal to 10%
    if abs(target) < 11:
        X.append(features)
        Y.append(target)

# Convert lists to numpy arrays
X = np.array(X)
Y = np.array(Y)

print(X,Y)
# Load the saved model
loaded_model = joblib.load("C:/Users/Antonio/Documents/MyProjects/BatteryInfo/linearModel/linear_regression_model.pkl")

# Now, you can use the trained model to make predictions
# Let's test it with a sample input (battery percentage differences)
sample_input = X[-1]  # Use the first set of battery percentage differences from the data

# Predict the battery percentage change
predicted_change = loaded_model.predict([sample_input])
print(predicted_change)

# Get the actual battery percentage data for a specific day in September
cur.execute(f"SELECT time, batteryPerc FROM {month} WHERE day='{day}';")
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
print(last_actual_point)
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
