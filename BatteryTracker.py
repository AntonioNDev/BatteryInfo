from tkinter import *
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sqlite3 as sql
import datetime

now = datetime.datetime.now()

day = now.strftime("%a %d")
month = now.strftime("%b")
year = now.strftime("%Y")

window = Tk()
window.title("Battery Tracker")
window.iconbitmap("logo/logoNBW.ico")

databasePath = 'C:/Users/Antonio/Documents/MyProjects/BatteryInfo/database.db'

conn = sql.connect(databasePath)
cur = conn.cursor()

class AppFunctions:
   def avgBattLife(self, xPoints, yPoints) -> int:
      pairs = []
      calc = []
      yPointIndices = {}

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

      # Build a dictionary of indices for the elements in yPoints
      for i, y in enumerate(yPoints):
         yPointIndices[y] = i
         
      # Iterate over the pairs of elements in pairs
      for i in range(0, len(pairs)-1, 2):
         if pairs[i] in yPoints:
               # Look up the indices of the elements in yPoints using the dictionary
               numz1 = yPointIndices[pairs[i]]
               numz2 = yPointIndices[pairs[i+1]]

               calc.append(abs(xPoints[numz1]-xPoints[numz2]))
      
      resultInMinutes = sum(calc) / len(calc)
      hours, minutes = self.minutesToHours(resultInMinutes)

      return hours

   def batteryCharged(self, yPoints):
      batteryChargedToday = 0

      for x in range(0, len(yPoints) - 1):
         if yPoints[x+1] < yPoints[x]:
            batteryChargedToday += 1

      return batteryChargedToday 
   
   def minutesToHours(self, total):
      hours = int(total) // 60 #Convert minutes in hours and minutes... 
      minutes = total % 60

      return hours, minutes

   def getData(self, month, day, year):
      Ypoints = np.array([])
      Xpoints = np.array([])

      xDataFAvg = []
      yDataFAvg = []

      if month and day and year:
         try:
            data = conn.execute(f"SELECT * FROM {month} WHERE day=? AND year=? AND time > 600;", (day, year)).fetchall()
            
            for i, x in enumerate(data):
               Ypoints = np.append(Ypoints, [x[0]])

               total_min = x[2]
               hours, minutes = self.minutesToHours(total_min)

               Xpoints = np.append(Xpoints, [f'{hours:02d}:{minutes:02d}']) 

               yDataFAvg.append(x[0])
               xDataFAvg.append(total_min)

            self.createGraph(Xpoints, Ypoints) #calls the function to create the graph

            batteryCharg = self.batteryCharged(Ypoints)
            averBatt = self.avgBattLife(xDataFAvg, yDataFAvg)

            #Labels for how many times batt was charged and average life of the battery
            batteryInfo.config(text=f"Battery Charged: {batteryCharg} time/s | Average battery life: ≈{averBatt:.1f}h") 

            errorLabel.config(text="")

         except Exception as e:
            errorLabel.config(text=f"{e}")
            
      else:
         errorLabel.config(text="Empty inputs!.")

   def helperFunc(self, month):
      try:
         selected = my_tree.focus()
         values = my_tree.item(selected, 'values')
         day = values[0]
         year = values[1]

         self.getData(month, day, year)
      except Exception as e:
         errorLabel.config(text=f"{e}")

   def searchQuery(self, month, year):
      my_tree.delete(*my_tree.get_children())
      if month and year:
         try:
            data = conn.execute(f"SELECT * FROM {month} WHERE year=?;", (int(year),)).fetchall()
            previusDate = ''

            for i, x in enumerate(data):
               if(x[1] != previusDate):
                  my_tree.insert(parent='', index='end', text='', values=(x[1], x[3]))

               previusDate = x[1]

            errorLabel.config(text="")
            dataFrame.configure(text=f'Data for: {month}')

         except Exception as e:
            errorLabel.config(text=f"{e}")
            
      else:
         errorLabel.config(text="Empty inputs!.")

   def createGraph(self, x, y):
      f = plt.Figure(figsize=(12, 5.5), dpi=75)
      ax = f.add_subplot()

      for i in range(1, len(y)):
         # Calculate the difference between consecutive y-values
         diff = y[i] - y[i-1]
         if diff <= -6:
            # If the difference is <= -6, use the line style and color for "High"
            lineStyle = "solid"
            color = 'red'
         elif diff <= -4:
            # If the difference is <= -4, use the line style and color for "Normal"
            lineStyle = "dashed"
            color = 'orange'
         else:
            # If the difference is > -4, use the line style and color for "Low"
            lineStyle = "dotted"
            color = 'green'

         # Plot the line segment with the appropriate line style and color
         ax.plot(x[i-1:i+1], y[i-1:i+1], c=color, linestyle=lineStyle)
      
      ax.set_xticks(range(len(x)))
      ax.set_xticklabels(x, rotation=35)

      ax.set_ylabel("Battery Percentage")
      ax.set_xlabel("Time")
      
      canvas = FigureCanvasTkAgg(f, graphFrame)
      canvas.get_tk_widget().grid(row=0, column=0)

class AppGUI: 
   def __init__(self):
      self.appWidth = 1250
      self.appHeight = 750
      self.screen_w = window.winfo_screenwidth()
      self.screen_h = window.winfo_screenheight()

      x = (self.screen_w / 2) - (self.appWidth) + 600
      y = (self.screen_h / 2) - (self.appHeight) + 350
      window.geometry(f'{self.appWidth}x{self.appHeight}+{int(x)}+{int(y)}')

      self.func = AppFunctions()

      self.main()

   def main(self):
      global errorLabel, graphFrame, batteryInfo, my_tree, dataFrame

      sideFrame = Frame(window, relief='sunken', height=self.appHeight, width=350, border=3)
      sideFrame.pack(side=LEFT)

      searchFrame = LabelFrame(sideFrame, height=130, width=350, bg='#ccd5ae', text='Month & Year')
      searchFrame.grid(row=0, column=0, sticky='n')

      dataFrame = LabelFrame(sideFrame, height=600, width=350, bg='#e5e5e5', relief='sunken', border=2, text=f'')
      dataFrame.grid(row=1, column=0)
      
      mainFrame = Frame(window, relief='sunken', height=500, width=1000)
      mainFrame.pack(side=RIGHT)

      #######################################################################################################################
      #records frame inputs and labels
      
      searchMonth = Entry(searchFrame, highlightthickness=1, border=2, font=('Arial', 9), justify=CENTER)
      searchMonth.grid(row=0, column=0, ipady=5, padx=10, pady=10)

      searchYear = Entry(searchFrame, highlightthickness=1, border=2, font=('Arial', 9), justify=CENTER)
      searchYear.grid(row=0, column=1, ipady=5, padx=10, pady=10)

      button = Button(searchFrame, border=2, text='Search', font=('Arial', 11), relief='groove', bg='#fefae0', cursor="hand2", command=lambda: self.func.searchQuery(searchMonth.get(), searchYear.get()))
      button.grid(row=1, column=0, pady=3, ipadx=15)
      button.configure(activebackground='#e9edc9')

      ###########################################Treeview#########################################################

      tree_scroll = Scrollbar(dataFrame)
      tree_scroll.pack(side=RIGHT, fill=Y)

      style = ttk.Style()
      style.theme_use("clam")  
      style.configure("Treeview",
         background="white",
         foreground="#231942",
         rowheight=25,
         fieldbackground="white"
      )


      my_tree = ttk.Treeview(dataFrame, yscrollcommand=tree_scroll.set)
      my_tree.pack(ipadx=50, ipady=160, fill=BOTH)

      tree_scroll.config(command=my_tree.yview)

      my_tree['columns'] = ("Day", "Year")

      my_tree.column("#0", width=0, stretch=NO)
      my_tree.column("Day", anchor=CENTER, width=100)
      my_tree.column("Year", anchor=CENTER, width=120)
      
      my_tree.heading("#0", text='', anchor=W)
      my_tree.heading("Day", text="Day", anchor=CENTER)
      my_tree.heading("Year", text="Year", anchor=CENTER)

      ####################################################################################################
      #bottom graph frame
      graphFrame = Frame(mainFrame, relief='sunken', border=3, height=self.appHeight, bg='#ffffff', width=900)
      graphFrame.grid(row=1, column=1)

      bottomInfoFrame = Frame(graphFrame, relief='groove', border=1, height=100, bg='#eaf4f4')
      bottomInfoFrame.pack(side=BOTTOM, fill=X)

      batteryInfo = Label(bottomInfoFrame, text=f"", bg='#eaf4f4', fg='#023047', font=('Arial', 10))
      batteryInfo.pack(side="bottom", pady=15)

      errorLabel = Label(bottomInfoFrame, text=f'', fg='#e63946')
      errorLabel.pack(side="bottom", pady=10)
      

      my_tree.bind("<Double-1>", lambda e: self.func.helperFunc(searchMonth.get()))

      graphFrame.pack_propagate(False)
      bottomInfoFrame.pack_propagate(False)
      searchFrame.grid_propagate(False)
      dataFrame.grid_propagate(False)
      graphFrame.grid_propagate(False)


      #Create graph when the app is started
      self.func.getData(month, day, year)

AppGUI()

window.bind('<Button>', lambda event: event.widget.focus_set())
window.resizable(False, False) 
window.mainloop()
