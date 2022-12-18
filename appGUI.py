from tkinter import *
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sqlite3 as sql

window = Tk()
window.title("Battery App GUI")

conn = sql.connect('C:/Users/Antonio/Documents/MyProjects/Battery/database.db')
cur = conn.cursor()

class AppGUI:
   def __init__(self):
      self.appWidth = 900
      self.appHeight = 700
      self.screen_w = window.winfo_screenwidth()
      self.screen_h = window.winfo_screenheight()

      x = (self.screen_w / 2) - (self.appWidth) + 450
      y = (self.screen_h / 2) - (self.appHeight) + 350
      window.geometry(f'{self.appWidth}x{self.appHeight}+{int(x)}+{int(y)}')

      self.main()

   def getIndexAndCalc(self, time, pairs, yPoints):
      calc = []
      yPointIndices = {}

      # Build a dictionary of indices for the elements in yPoints
      for i, y in enumerate(yPoints):
         yPointIndices[y] = i

      # Iterate over the pairs of elements in pairs
      for i in range(0, len(pairs)-1, 2):
         if pairs[i] in yPoints:
               # Look up the indices of the elements in yPoints using the dictionary
               numz1 = yPointIndices[pairs[i]]
               numz2 = yPointIndices[pairs[i+1]]
               calc.append(abs(time[numz1]-time[numz2]))

      result = sum(calc) / len(calc) + 0.9

      return result

   def avgBattLife(self, xPoints, yPoints):
      pairs = []

      startIndex = 0
      sublist = yPoints[:]
      # iterate over the numbers in the list
      for i in range(0, len(yPoints)-1):
         if yPoints[i] < yPoints[i+1]:
            sublist = yPoints[startIndex:i+1]
            min_num = min(sublist)
            max_num = max(sublist)
                                          #Iterates over the list and it separates the numbers by slicing
            pairs.append(max_num)         #Then it sends to the function where it finds the index of the numbers
            pairs.append(min_num)         #And it calculates how many hours the battery lasted (approximately).
                                          
            startIndex = i+1
               

      restOfTheNums = yPoints[startIndex:len(yPoints)]
      min_num = min(restOfTheNums) 
      max_num = max(restOfTheNums)

      pairs.append(max_num)
      pairs.append(min_num)


      result = self.getIndexAndCalc(xPoints, pairs, yPoints)
      return result

   def batteryCharged(self, yPoints):
      batteryChargedToday = 0

      for x in range(0, len(yPoints) - 1):
         if yPoints[x+1] > yPoints[x]:
            batteryChargedToday += 1

      return batteryChargedToday

   def createGraph(self, x, y):
      f = plt.Figure(figsize=(11.5, 5.7), dpi=80)
      f.add_subplot().plot(x, y)
      
      canvas = FigureCanvasTkAgg(f, bottomFrame)
      canvas.get_tk_widget().grid(row=0, column=0)

   def getData(self, month, day, year):
      Ypoints = np.array([])
      Xpoints = np.array([])

      xDataFAvg = []
      yDataFAvg = []

      if month and day and year:
         try:
            data = conn.execute(f"SELECT * FROM {month} WHERE day=? AND year=?;", (day, year)).fetchall()
            
            for i, x in enumerate(data):
               Ypoints = np.append(Ypoints, [x[0]])

               total_min = x[2]
               hours = int(total_min) // 60 #Convert minutes in hours, minutes... 
               minutes = total_min % 60

               Xpoints = np.append(Xpoints, [f'{hours:02d}:{minutes:02d}']) 

               yDataFAvg.append(x[0])
               xDataFAvg.append(hours)


            self.createGraph(Xpoints, Ypoints)

            batteryCharg = self.batteryCharged(Ypoints)
            averBatt = self.avgBattLife(xDataFAvg, yDataFAvg)

            timesChargedLabel.config(text=f"Battery Charged: {batteryCharg} time/s.") #Labels for how many times batt was charged and average life of the battery
            avgBattLife.config(text=f"Battery was charged every: ≈{averBatt:.1f}h")

            errorLabel.config(text="")


         except Exception as e:
            print(e)
            errorLabel.config(text="No data for that month/day/year. Try again!.")

      else:
         errorLabel.config(text="Empty inputs!.")

   def main(self):
      global errorLabel, bottomFrame, timesChargedLabel, avgBattLife

      mainFrame = Frame(window, relief='sunken', bg='red', height=500)
      mainFrame.pack(fill=BOTH)

      topFrame = Frame(mainFrame, relief='sunken', border=3, height=250, bg='#81b29a')
      topFrame.grid(row=0, column=0, ipadx=self.appWidth)

      ########## top frame inputs and labels ###########
      monthLabel = Label(topFrame, text='Month', font=('Lucida Bright', 18), bg='#81b29a')
      monthLabel.grid(row=0, column=0, padx=115)

      monthEntry = Entry(topFrame, highlightthickness=1, border=2, font=('Lucida Bright', 14), justify=CENTER)
      monthEntry.grid(row=1, column=0)

      ####
      dayLabel = Label(topFrame, text='Day/Date', font=('Lucida Bright', 18), bg='#81b29a')
      dayLabel.grid(row=0, column=1, padx=30, pady=30)

      dayEntry = Entry(topFrame, highlightthickness=1, border=2, font=('Lucida Bright', 14), justify=CENTER)
      dayEntry.grid(row=1, column=1)

      ####
      yearLabel = Label(topFrame, text='Year', font=('Lucida Bright', 18), bg='#81b29a')
      yearLabel.grid(row=0, column=2, padx=130, pady=30)

      yearEntry = Entry(topFrame, highlightthickness=1, border=2, font=('Lucida Bright', 14), justify=CENTER)
      yearEntry.grid(row=1, column=2)

      errorLabel = Label(topFrame, text=f'', font=('Lucida Bright', 10), bg='#81b29a', fg='red')
      errorLabel.grid(row=2, column=1, pady=15)

      button = Button(topFrame, border=2, text='Get', font=('Lucida Bright', 13), relief='groove', bg='#fefae0', cursor="hand2", command=lambda: self.getData(monthEntry.get(), dayEntry.get(), yearEntry.get()))
      button.grid(row=3, column=1, pady=5, ipadx=50, ipady=10)
      button.configure(activebackground='#e9edc9')

      timesChargedLabel = Label(topFrame, text=f"", bg='#81b29a', fg='#fefae0', font=('San Serif', 10))
      timesChargedLabel.grid(row=2, column=2)

      avgBattLife = Label(topFrame, text=f"", bg='#81b29a', fg='#fefae0', font=('San Serif', 10))
      avgBattLife.grid(row=3, column=2)
      #######################################################################################################################


      bottomFrame = Frame(mainFrame, relief='sunken', border=3, height=600)
      bottomFrame.grid(row=1, column=0, ipadx=self.appWidth)
      

      topFrame.grid_propagate(False)
      bottomFrame.grid_propagate(False)

AppGUI()
window.bind('<Button>', lambda event: event.widget.focus_set())
window.resizable(False, False) 
window.mainloop()
