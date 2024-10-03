import sqlite3
import datetime
import time
import threading

import psutil
import logging


def configure_settings():
   import os

   global databasePath, logsPath, settingsPath, py_file

   appdata_path = os.getenv('APPDATA')
   app_folder = os.path.join(appdata_path, 'BatteryInfo')

   databasePath = os.path.join(app_folder, 'database.db')
   logsPath = os.path.join(app_folder, 'logs')
   settingsPath = os.path.join(app_folder, 'linearModel/settings.json')
   py_file = os.path.join(app_folder, 'linearModel/trainModel.pyw')


   logging.basicConfig(filename=f'{logsPath}/errorLogs.log', level=logging.ERROR, format='%(levelname)s-%(message)s')

class App:
   def __init__(self):
      self.month = datetime.datetime.now().strftime("%b")

      x = threading.Thread(target=self.trainModel)
      x.start()

      #Check if the month table exists in the database.
      self.create_table(self.month)
      self.main()

   def trainModel(self):
      import json
      from datetime import datetime
      import subprocess

      try: 
         # Load the data
         with open(f'{settingsPath}', 'r') as txt:
            data = json.load(txt)
         
         current_date = datetime.now().strftime('%d.%m.%Y') # Get the current date
         
         last_increment = data.get('last_increment', '') # Check if the day has already been incremented today

         if last_increment != current_date:  # Only increment if not already done today
            data['day'] += 1
            data['last_increment'] = current_date

            # If 30 days have passed, retrain the model
            if data['day'] >= 30:
                  data['day'] = 0  # Reset the day counter after training

                  # Call the trainModel.pyw file
                  subprocess.Popen(['python', f'{py_file}'])

         # Save the updated settings back to the JSON file
         with open(f'{settingsPath}', 'w') as txt:
            json.dump(data, txt, indent=4)

      except Exception as e:
         logging.error(f'Something went wrong with training the model: {e}')

   def create_table(self, month):
      with sqlite3.connect(databasePath) as conn:
         cur = conn.cursor()
         cur.execute(f"""CREATE TABLE IF NOT EXISTS {month} (
               batteryPerc INT NOT NULL,
               day TEXT NOT NULL,
               time INT NOT NULL,
               year TEXT NOT NULL
         );""")
         conn.commit()

   def write_data(self, percentage, day, time, month, year):
      try:
         with sqlite3.connect(databasePath) as conn:
            cur = conn.cursor()
            cur.execute(f"INSERT INTO {month} VALUES (?, ?, ?, ?)", (percentage, day, time, year))
            conn.commit()

      except Exception as e:
         logging.error(f'{day}: {e}')

   def main(self):
      while True:
         now = datetime.datetime.now()
         time_in_minutes = now.hour * 60 + now.minute
         battery_info = psutil.sensors_battery()

         day = now.strftime("%a %d")
         month = now.strftime("%b")
         year = now.strftime("%Y")


         if battery_info.power_plugged != True:
               self.write_data(battery_info.percent, day, time_in_minutes, month, year)

         #get battery percentage every 15 minutes
         time.sleep(900)
         
if __name__ == '__main__':
   configure_settings()
   App()