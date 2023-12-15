import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()
months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'dec']
for month in months:
   cursor.execute(f"""
   SELECT day, COUNT(*) AS num_points
   FROM {month}
   GROUP BY day
   """)

   total_points = 0
   total_days = 0
   for row in cursor.fetchall():
      day, num_points = row
      total_points += num_points
      total_days += 1

   average_points_per_day = total_points / total_days
   print(f"Average data points saved for {month}: {average_points_per_day:.2f}")

# Close the connection
conn.close()
