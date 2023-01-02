from tkinter import *
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sqlite3 as sql

window = Tk()
window.title("Battery Info")

databasePath = 'C:/Users/Antonio/Documents/MyProjects/BatteryInfo/database.db'

conn = sql.connect(databasePath)
cur = conn.cursor()

class AppGUI:
   def __init__(self):
      self.appWidth = 1250
      self.appHeight = 750
      self.screen_w = window.winfo_screenwidth()
      self.screen_h = window.winfo_screenheight()

      x = (self.screen_w / 2) - (self.appWidth) + 600
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

      result = sum(calc) / len(calc) + 0.8

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
      f = plt.Figure(figsize=(13, 6), dpi=70)
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

            #Labels for how many times batt was charged and average life of the battery
            batteryInfo.config(text=f"Battery Charged: {batteryCharg} time/s | Average battery life: ≈{averBatt:.1f}h") 

            errorLabel.config(text="")

         except Exception as e:
            print(e)
            errorLabel.config(text="No data for that month/day/year. Try again!.")

      else:
         errorLabel.config(text="Empty inputs!.")

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
            errorLabel.config(text="No data for that month/day/year. Try again!.")

      else:
         errorLabel.config(text="Empty inputs!.")


   def main(self):
      global errorLabel, bottomFrame, batteryInfo, my_tree, dataFrame

      sideFrame = Frame(window, relief='sunken', height=self.appHeight, width=350, border=3)
      sideFrame.pack(side=LEFT)

      searchFrame = LabelFrame(sideFrame, height=130, width=350, bg='#ccd5ae', text='Month & Year')
      searchFrame.grid(row=0, column=0, sticky='n')

      dataFrame = LabelFrame(sideFrame, height=600, width=350, bg='#e5e5e5', relief='sunken', border=2, text=f'')
      dataFrame.grid(row=1, column=0)
      
      mainFrame = Frame(window, relief='sunken', height=500, width=1000)
      mainFrame.pack(side=RIGHT)

      topFrame = Frame(mainFrame, relief='sunken', border=3, height=250, bg='#81b29a', width=900)
      topFrame.grid(row=0, column=1)

      ########## top frame inputs and labels ###########
      monthLabel = Label(topFrame, text='Month', font=('Lucida Bright', 17), bg='#81b29a')
      monthLabel.grid(row=0, column=0, padx=115)

      monthEntry = Entry(topFrame, highlightthickness=1, border=2, font=('Lucida Bright', 14), justify=CENTER)
      monthEntry.grid(row=1, column=0)

      ####
      dayLabel = Label(topFrame, text='Day/Date', font=('Lucida Bright', 17), bg='#81b29a')
      dayLabel.grid(row=0, column=1, padx=30, pady=30)

      dayEntry = Entry(topFrame, highlightthickness=1, border=2, font=('Lucida Bright', 14), justify=CENTER)
      dayEntry.grid(row=1, column=1)

      ####
      yearLabel = Label(topFrame, text='Year', font=('Lucida Bright', 17), bg='#81b29a')
      yearLabel.grid(row=0, column=2, padx=130, pady=30)

      yearEntry = Entry(topFrame, highlightthickness=1, border=2, font=('Lucida Bright', 14), justify=CENTER)
      yearEntry.grid(row=1, column=2)

      errorLabel = Label(topFrame, text=f'', font=('Lucida Bright', 10), bg='#81b29a', fg='red')
      errorLabel.grid(row=2, column=1, pady=15)

      button = Button(topFrame, border=2, text='Show graph', font=('Lucida Bright', 12), relief='groove', bg='#fefae0', cursor="hand2", command=lambda: self.getData(monthEntry.get(), dayEntry.get(), yearEntry.get()))
      button.grid(row=3, column=1, pady=1, ipadx=30, ipady=5)
      button.configure(activebackground='#e9edc9')

      
      #######################################################################################################################
      #records frame inputs and labels
      
      searchMonth = Entry(searchFrame, highlightthickness=1, border=2, font=('Arial', 9), justify=CENTER)
      searchMonth.grid(row=0, column=0, ipady=5, padx=10, pady=10)

      searchYear = Entry(searchFrame, highlightthickness=1, border=2, font=('Arial', 9), justify=CENTER)
      searchYear.grid(row=0, column=1, ipady=5, padx=10, pady=10)

      button = Button(searchFrame, border=2, text='Search', font=('Arial', 11), relief='groove', bg='#fefae0', cursor="hand2", command=lambda: self.searchQuery(searchMonth.get(), searchYear.get()))
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
      bottomFrame = Frame(mainFrame, relief='sunken', border=3, height=500, bg='#ffffff', width=900)
      bottomFrame.grid(row=1, column=1)

      bottomInfoFrame = Frame(bottomFrame, relief='groove', border=1, height=75, bg='#eaf4f4')
      bottomInfoFrame.pack(side=BOTTOM, fill=X)

      batteryInfo = Label(bottomInfoFrame, text=f"", bg='#eaf4f4', fg='#023047', font=('Arial', 10))
      batteryInfo.pack(side="bottom", pady=15)
      

      my_tree.bind("<Double-1>", my_tree.focus())
      bottomFrame.pack_propagate(False)
      bottomInfoFrame.pack_propagate(False)
      searchFrame.grid_propagate(False)
      dataFrame.grid_propagate(False)
      topFrame.grid_propagate(False)
      bottomFrame.grid_propagate(False)


AppGUI()

window.bind('<Button>', lambda event: event.widget.focus_set())
window.resizable(False, False) 
window.mainloop()
