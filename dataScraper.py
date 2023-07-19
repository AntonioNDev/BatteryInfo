import sqlite3 as sql
import matplotlib.pyplot as plt

# Connect to the database
databasePath = 'C:/Users/Antonio/Documents/MyProjects/BatteryInfo/database.db'
conn = sql.connect(databasePath)
cur = conn.cursor()

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def batteryCharged(yPoints):
   batteryChargedCount = 0

   for x in range(len(yPoints) - 1):
      if yPoints[x + 1] > yPoints[x]:
         batteryChargedCount += 1

   return batteryChargedCount


def yearly():
   chargedCounts = []
   for month in months:
      data = conn.execute(f"SELECT * FROM {month};").fetchall()
      points = [row[0] for row in data]
      chargedCounts.append(batteryCharged(points))

   # Create a line plot
   plt.plot(months, chargedCounts, marker='o', linestyle='-', color='b')
   plt.xlabel('Month')
   plt.ylabel('Charging Count')
   plt.title('Battery Charging Count per Month')

   # Add labels on each data point
   for month, count in zip(months, chargedCounts):
      plt.text(month, count, str(count), ha='center', va='bottom')

   plt.show()


yearly()