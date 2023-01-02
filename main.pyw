import sqlite3
import datetime
import time

import psutil
import logging

path = "C:/Users/Antonio/Documents/MyProjects/BatteryInfo/logs"
databasePath = 'C:/Users/Antonio/Documents/MyProjects/BatteryInfo/database.db'

logging.basicConfig(filename=f'{path}/errorLogs.log', level=logging.ERROR, format='%(levelname)s-%(message)s')

class App:
   def __init__(self):
      self.month = datetime.datetime.now().strftime("%b")

      #Check if the month table exists in the database.
      self.create_table(self.month)

   def create_table(self, month):
      with sqlite3.connect(databasePath) as conn:
         cur = conn.cursor()
         cur.execute(f"""CREATE TABLE IF NOT EXISTS {month} (
               battery_perc INT NOT NULL,
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
   App().main()