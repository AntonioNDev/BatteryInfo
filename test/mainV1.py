import sqlite3
import datetime
import time

import matplotlib.pyplot as plt
import numpy as np
import psutil
import logging

conn = sqlite3.connect('C:/Users/Antonio/Documents/MyProjects/Battery/database.db')
cur = conn.cursor()

path = "C:/Users/Antonio/Documents/MyProjects/Battery/logs"
logging.basicConfig(filename=f'{path}/appLogs.log', level=logging.INFO, format='%(levelname)s-%(message)s')

class App:
   def __init__(self):
      self.Ypoints = np.array([])
      self.Xpoints = np.array([])
      self.batteryChargedToday = 0
      self.month = datetime.datetime.now().strftime("%b")

      #Create table if does not exists.
      self.create_table(self.month)

   def create_table(self, month):
      conn.execute(f"""CREATE TABLE IF NOT EXISTS {month} (
               batteryPerc INT NOT NULL,
               day TXT NOT NULL,
               time INT NOT NULL,
               year TXT NOT NULL
      );""")
      conn.commit()
      
   def write_data(self, percentage, day, time, month, year):
      conn.execute(f"INSERT INTO {month} VALUES ('{percentage}', '{day}', '{time}', '{year}')")
      conn.commit()

   #Check how many times the battery was charged 
   #If x[x+1] > x[x] that means if x[60] > x[30] the battery was charged.
   def battCharged(self, batteryP):
      for x in range(0, len(batteryP) - 1):
         if batteryP[x+1] > batteryP[x]:
            self.batteryChargedToday += 1

      return self.batteryChargedToday

   def create_GraphImg(self, month, day):
      data = conn.execute(f"SELECT * FROM {month} WHERE day='{day}'")
      fetchData = data.fetchall()

      for x in range(len(fetchData)):
         self.Ypoints = np.append(self.Ypoints, [fetchData[x][0]])
         
         total_min = fetchData[x][2]
         hours = int(total_min) // 60
         minutes = total_min % 60

         self.Xpoints = np.append(self.Xpoints, [f'{hours}:{minutes}']) 

      battCharged = self.battCharged(self.Ypoints) #how many times battery was charged

      plt.figtext(0.01, 0.01, f"Battery charged: {battCharged} time/s")
      plt.plot(self.Xpoints, self.Ypoints)
      plt.savefig(f"C:/Users/Antonio/Documents/MyProjects/Battery/info/graph({month} -- [{day}]).jpg")
      
      logging.info(f'[{day}] graph created.')

   def main(self):
      while True: 
         timeNow = datetime.datetime.now().strftime("%H:%M") #time
         timeInMinutes = int(timeNow[:2]) * 60 + int(timeNow[3:]) #Convert hours in minutes
         batteryInfo = psutil.sensors_battery() #Get battery percentage 

         day = datetime.datetime.now().strftime("%a %d") #Get day, month and year
         month = datetime.datetime.now().strftime("%b") 
         year = datetime.datetime.now().strftime("%Y")  
         
         if int(timeNow[:2]) == 23 and int(timeNow[3:]) > 30: # If time is more than 23:30 then new graph will be created
            self.create_GraphImg(month, day) #Calling func to create the graph

         else:
            #If battery is not plugged write data
            if batteryInfo.power_plugged != True:
               self.write_data(batteryInfo.percent, day, timeInMinutes, month, year)
               logging.info(f'Added: Battery percentage: {batteryInfo.percent} | timeNow: {timeNow} | timeInMinutes: {timeInMinutes}')


         #Get info every 30 minutes (1800sec)
         time.sleep(1800)


if __name__ == '__main__':
   App().main()