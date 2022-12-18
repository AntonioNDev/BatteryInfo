from functools import reduce
import sqlite3
import numpy as np

conn = sqlite3.connect('C:/Users/Antonio/Documents/MyProjects/Battery/database.db')
cur = conn.cursor()

data = conn.execute("SELECT * FROM Dec WHERE day = 'Mon 12';").fetchall()


bp = []
time = []

for x in range(len(data)):
   
   batteryPerc = data[x][0]
   total_min = data[x][2]

   hours = int(total_min) // 60
   
   bp.append(batteryPerc)
   time.append(hours)


print(bp, time)

def getIndexAndCalc(time, pairs, bp):
   indexOfLastNum = 0
   calc = []

   for i in range(0, len(pairs)-1, 2):
      if pairs[i] in bp:
         numz1 = bp.index(pairs[i], indexOfLastNum, len(bp))
         numz2 = bp.index(pairs[i+1], indexOfLastNum, len(bp))
         calc.append(abs(time[numz1]-time[numz2]))
         print(numz1, numz2)
         indexOfLastNum = bp.index(pairs[i+1])

   return reduce(lambda x,y: x+y, calc)/len(calc) + 1.5
   
def getIndexAndCalc2(time, pairs, yPoints):
      calc = []
      yPointIndices = {}

      # Build a dictionary of indices for the elements in yPoints
      for i, y in enumerate(yPoints):
         yPointIndices[y] = i

      print(f"dict: {yPointIndices}")

      # Iterate over the pairs of elements in pairs
      for i in range(0, len(pairs)-1, 2):
         print("i is", i)
         if pairs[i] in yPoints:
               # Look up the indices of the elements in yPoints using the dictionary
               numz1 = yPointIndices[pairs[i]]
               numz2 = yPointIndices[pairs[i+1]]
               print(f"num1: {numz1} | num2: {numz2}")
               calc.append(abs(time[numz1]-time[numz2]))

      result = sum(calc)/len(calc) + 1

      return result

def avgr(bp, time):
   pairs = []

   startIndex = 0
   sublist = bp[:]
   # iterate over the numbers in the list
   for i in range(0, len(bp)-1):
      if bp[i] < bp[i+1]:
         sublist = bp[startIndex:i+1]
         min_num = min(sublist)
         max_num = max(sublist)

         pairs.append(max_num)
         pairs.append(min_num)
         startIndex = i+1
            


   restOfTheNums = bp[startIndex:len(bp)]
   min_num = min(restOfTheNums)
   max_num = max(restOfTheNums)

   pairs.append(max_num)
   pairs.append(min_num)


   print(getIndexAndCalc2(time, pairs, bp))
         


   
avgr(bp, time)
