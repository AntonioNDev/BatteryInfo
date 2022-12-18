import sqlite3
import datetime
import time

import matplotlib.pyplot as plt
import numpy as np
import psutil
import logging

path = "C:/Users/Antonio/Documents/MyProjects/Battery/logs"
logging.basicConfig(filename=f'{path}/appLogs.log', level=logging.ERROR, format='%(levelname)s-%(message)s')

class App:
   def __init__(self):
      self.y_points = np.array([])
      self.x_points = np.array([])
      self.battery_charged_today = 0
      self.month = datetime.datetime.now().strftime("%b")

      #Check if the month table exists in the database.
      self.create_table(self.month)

   def create_table(self, month):
      with sqlite3.connect('C:/Users/Antonio/Documents/MyProjects/Battery/database.db') as conn:
         cur = conn.cursor()
         cur.execute(f"""CREATE TABLE IF NOT EXISTS {month} (
               battery_perc INT NOT NULL,
               day TXT NOT NULL,
               time INT NOT NULL,
               year TXT NOT NULL
         );""")

   def write_data(self, percentage, day, time, month, year):
      with sqlite3.connect('C:/Users/Antonio/Documents/MyProjects/Battery/database.db') as conn:
         cur = conn.cursor()
         cur.execute(f"INSERT INTO {month} VALUES (?, ?, ?, ?)", (percentage, day, time, year))
         conn.commit()

   def batt_charged(self, battery_perc):
      for i in range(len(battery_perc) - 1):
         if battery_perc[i + 1] > battery_perc[i]:
               self.battery_charged_today += 1

      return self.battery_charged_today

   def create_graph_img(self, month, day, year):
      try:
         with sqlite3.connect('C:/Users/Antonio/Documents/MyProjects/Battery/database.db') as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {month} WHERE day=? AND year=?", (day, year,))
            fetch_data = cur.fetchall()

            for i in range(len(fetch_data)):
                  self.y_points = np.append(self.y_points, [fetch_data[i][0]])

                  total_min = fetch_data[i][2]

                  hours = int(total_min) // 60
                  minutes = total_min % 60

                  self.x_points = np.append(self.x_points, [f'{hours}:{minutes}']) 

            batt_charged = self.batt_charged(self.y_points) #how many times battery was charged

            plt.figtext(0.01, 0.01, f"Battery charged: {batt_charged} time/s")
            plt.plot(self.x_points, self.y_points)
            plt.savefig(f"C:/Users/Antonio/Documents/MyProjects/Battery/info/graph({month}--[{day}]).jpg")
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

         if now.hour == 23 and now.minute > 30:
            self.create_graph_img(month, day, year)
         else:
            try:
               if battery_info.power_plugged != True:
                  self.write_data(battery_info.percent, day, time_in_minutes, month, year)
                  logging.info(f'Added: Battery percentage: {battery_info.percent} | timeNow: {now.hour}:{now.minute} | timeInMinutes: {time_in_minutes}')

            except Exception as e:
               logging.error(f'{day}: {e}')
               
         #get battery percentage every 30 minutes
         time.sleep(1800)
         

if __name__ == '__main__':
   App().main()