import sqlite3
import numpy as np
import joblib
import logging
import psutil
import os
import datetime
from sklearn.metrics import mean_absolute_error

log_folder = ""
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

# Set up logging with a custom format
log_filename = f'{log_folder}/modelInfo.log'
logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

conn = sqlite3.connect('database.db')
cur = conn.cursor()

class ModelStats:
   def __init__(self):
      self.model = joblib.load('C:/Users/Antonio/Documents/MyProjects/BatteryInfo/linearModel/linear_regression_model.pkl')
      self.correct_predictions = 0
      self.total_predictions = 0
      self.total_error = 0.0
      self.interval = 2


      self.main()

   def prepare_data(self, data):
      X = []
      Y = []
      for i in range(len(data) - self.interval):
         features = data[i:i+self.interval, 1]  # Battery percentage values
         target = data[i+self.interval, 1] - data[i, 1]  # Battery percentage change over the interval

         # Exclude differences greater than or equal to 10%
         if abs(target) < 11:
            X.append(features)
            Y.append(target)

      # Convert lists to numpy arrays
      X = np.array(X)
      Y = np.array(Y)
      
      sample_input = X[-1]

      return sample_input

   def predict(self):

      now = datetime.datetime.now()
      current_day = now.strftime("%a %d")
      current_month = now.strftime("%b")

      cur.execute(f"SELECT time, batteryPerc FROM {current_month} WHERE day = ?", (current_day,))
      data = cur.fetchall()
      data = np.array(data)

      predicted_change = self.model.predict([self.prepare_data(data)])
      last_actual_data = data[-1, 1]

      predicted_battery = int([last_actual_data + np.sum(predicted_change[:i+1]) for i in range(len(predicted_change))][0])

      return predicted_battery


   def main(self):
      import time
      while True:
         if psutil.sensors_battery().power_plugged == False:
            feature = self.predict()

            time.sleep(910) #get battery and wait for the predicted value 15 minutes. 
            
            current_battery = psutil.sensors_battery().percent
            mae = mean_absolute_error([current_battery], [feature])

            self.total_predictions += 1
            self.total_error += mae

            if abs(current_battery - feature) <= 3.0:  # Define a threshold for correctness
               self.correct_predictions += 1

            logging.info(f"Date/Time: {datetime.datetime.now()} | CurrentBP: {current_battery} | PredictedBP: {feature} | MAError: {mae}")
            
            try:
               logging.info(f"Date/Time: {datetime.datetime.now()} | Total Predictions: {self.total_predictions if self.total_predictions > 0 else 0} | Correct Pred: {self.correct_predictions if self.correct_predictions > 0 else 0} | Accuracy: {(self.correct_predictions / self.total_predictions * 100) if self.total_predictions > 0 else 0} | MeanABS: {(self.total_error / self.total_predictions) if self.total_predictions > 0 else 0} /n/t")
           
            except Exception as e:
               logging.info(f"Date/Time: {datetime.datetime.now()} | error: {e}")
               pass 


