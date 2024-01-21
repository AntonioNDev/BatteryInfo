from tkinter import *
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import sqlite3 as sql
import datetime
import matplotlib.pyplot as plt
import gc
import numpy as np
import threading
import matplotlib

matplotlib.use('TkAgg')
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

# animations is not currently used but it will be future for menu sliding and other animations
class animations:
   def __init__(self) -> None:
      pass

# colorPallete is for the colors of the app
class colorPalette:
   def __init__(self) -> None:
      self.primaryC = '#b5bab7'
      self.secondaryC = '#D0CDCF'
      self.accentC = '#656C67'

# AppFunctions with all methods for the app
class AppFunctions:
   def __init__(self) -> None:
      self.stack = NavigationStack()
      self.months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

   def backButton(self): # returns to the previus graph
      self.stack.pop_call(self)

   def avgBattLife(self, xPoints, yPoints) -> list:
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
               
      rest_of_the_nums = yPoints[startIndex:]
      pairs.extend((max(rest_of_the_nums), min(rest_of_the_nums)))

      # Build a dictionary of indices for the elements in yPoints
      for i, y in enumerate(yPoints):
         yPointIndices[y] = i
         
      # Iterate over the pairs of elements in pairs
      for i in range(0, len(pairs) - 1, 2):
         if pairs[i] in yPoints:
               # Look up the indices of the elements in yPoints using the dictionary
               numz1 = yPointIndices[pairs[i]]
               numz2 = yPointIndices[pairs[i+1]]

               calc.append(abs(xPoints[numz1]-xPoints[numz2])) # xPoints[numz1] and xPoints[numz2] will subtract the minutes between the pairs

      resultInMinutes = sum(calc) / len(calc)
      hours, minutes = self.minutesToHours(resultInMinutes)

      return [hours, minutes]

   def batteryCharged(self, yPoints) -> int:
      batteryChargedToday = 0

      for x in range(len(yPoints) - 1):
         if yPoints[x+1] > yPoints[x]:
            batteryChargedToday += 1

      return batteryChargedToday 
   
   def minutesToHours(self, total) -> tuple:
      hours = int(total) // 60 #Convert minutes in hours and minutes... 
      minutes = total % 60

      return hours, minutes
   
   def getData(self, month, day, year):
      Ypoints = np.array([])
      Xpoints = np.array([])

      xDataFAvg = []
      yDataFAvg = []
      model_data = []

      if month and day and year:
         try:
            data = conn.execute(f"SELECT * FROM {month} WHERE day=? AND year=?", (day, year)).fetchall()
            for i, x in enumerate(data):
               Ypoints = np.append(Ypoints, [x[0]])

               total_min = x[2]
               hours, minutes = self.minutesToHours(total_min)

               Xpoints = np.append(Xpoints, [f'{hours:02d}:{minutes:02d}']) 

               yDataFAvg.append(x[0])
               xDataFAvg.append(total_min)
               model_data.append((x[2], x[0]))

            model_data = np.array(model_data)
            
            self.createGraph(Xpoints, Ypoints, day) #calls the function to create the graph

            if now.strftime("%a %d") == day and len(Xpoints) >= 3: #It works only on the current day, when there are more than 3 xpoints
               threading.Thread(target=self.linear_model, args=(model_data, Xpoints, Ypoints), daemon=True).start()#linear function thread so it doesn't slow down the main thread              

            batteryCharg = self.batteryCharged(Ypoints)#get battery charged count
            averBatt = self.avgBattLife(xDataFAvg, yDataFAvg)# get avg battery

            #Labels for how many times batt was charged and average life of the battery
            battery_info.config(text=f"Average batter: ≈{averBatt[0]}h:{averBatt[1]:.0f}m | Battery charged: {batteryCharg} {"times" if batteryCharg > 1 else "time"}")            
            
            errorLabel.config(text="")#clear errorLabel

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

         self.stack.add(self.getData, month, day, year)
         
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

   def prepare_data(self, data) -> np.ndarray: #interval=2 is how many samples will the model accept, because it's trained to work with 2, it only needs 2 samples
      X = []

      for i in range(0, len(data) - 1):
         target = data[i, 1] - data[i+1, 1]  #Battery percentage change over the interval
         print(f"{data[i+1,1]}-{data[i,1]}={target}")
         #Exclude differences greater than 13%
         if abs(target) < 12:
            X.append(abs(target))

      #Convert lists to numpy arrays
      X = np.array(X)
      print(f"X:{X}")
      sample_input = X[-2:]
      print(sample_input)

      return sample_input
   
   def linear_model(self, data, x, y):
      try: 
         import joblib
         self.model = joblib.load("C:/Users/Antonio/Documents/MyProjects/BatteryInfo/linearModel/linear_regression_model.pkl")
         
         predicted_change = self.model.predict([self.prepare_data(data)])
         last_actual_data = data[-1, 1]

         predicted_battery = int(np.sum([last_actual_data + np.sum(predicted_change[:i+1]) for i in range(len(predicted_change))]))

         last_x = x[-1]  #Last x value from the actual data
         last_y = y[-1]  #Last y value from the actual data

         #Extend y to include the predicted point
         y = np.append(y, predicted_battery)

         if canvas:
            #Connect the actual data endpoint with the predicted point
            ax.plot([last_x, len(x)], [last_y, predicted_battery], c='gray', linestyle='solid')

            # Extend x to include the position for "later" and set the last label
            x = np.append(x, len(x))
            x_labels = list(x)  #Convert x to a list to modify it
            x_labels[-1] = 'later'  #Set the last label to 'later'
            ax.set_xticks(x)
            ax.set_xticklabels(x_labels)

            ax.scatter([len(x) - 1], [predicted_battery], color='black', s=15, marker='o', linewidth=2, zorder=5)
            ax.annotate(f'{predicted_battery}%', (len(x) - 1, predicted_battery), textcoords='offset points', xytext=(-15, -5), ha='center', fontsize=11, color='black')

            canvas.draw()
      
      except Exception as e:
         errorLabel.config(text=f'Something went wrong with the linear model: {e}.')  
   
   def clearGraphs(self, gcC=False): #This function is used to clear the graph so there's not any duplicate graphs
      global f, ax, canvas, toolbar

      if 'canvas' in globals():
         canvas.get_tk_widget().destroy()

      if 'toolbar' in globals():
         toolbar.destroy()
         del toolbar

      if gcC:
         gc.collect()

   def createGraph(self, x, y, day):
      self.clearGraphs(True)
      global f, ax, canvas, toolbar

      f = plt.Figure(figsize=(16, 6), dpi=75) #NOTE: ADD YEARLY, MONTHY, WEEKLY usage of battery (time), how much times was charged...
      ax = f.add_subplot()

      for i in range(1, len(y)):
         # Calculate the difference between consecutive y-values
         diff = y[i] - y[i-1]
         
         if diff <= -6:
            #If the difference is <= -6, use the line style and color for "High"
            lineStyle = "solid"
            color = 'red'
         elif diff <= -4:
            #If the difference is <= -4, use the line style and color for "Normal"
            lineStyle = "dashed"
            color = 'orange'
         else:
            #If the difference is > -4, use the line style and color for "Low"
            lineStyle = "dotted"
            color = 'green'

         #Plot the line segment with the appropriate line style and color
         ax.plot(x[i-1:i+1], y[i-1:i+1], c=color, linestyle=lineStyle)

      minimum = min(y)  # Find the minimum y value
      for i in range(1, len(y)):
         if y[i] > y[i - 1]:
            ax.scatter([x[i]], [y[i]], color='black', s=30, marker='o', linewidth=2, zorder=5)
            ax.annotate('Charged', (x[i], y[i]), textcoords='offset points', xytext=(-30, 0), ha='center', fontsize=11, color='black')

         if y[i] == minimum:
            ax.scatter([x[i]], [y[i]], color='black', s=30, marker='o', linewidth=2, zorder=5)
            ax.annotate(f'Lowest {minimum:.0f}%', (x[i], y[i]), textcoords='offset points', xytext=(-40, 0), ha='center', fontsize=11, color='black')

      ax.set_xticks(range(len(x)))
      ax.set_xticklabels(x, rotation=35)

      ax.set_ylabel("Battery Percentage")
      ax.set_xlabel("Time")
      ax.set_title(f'Battery data for {day}')

      # Manually specify the legend entries for red, orange, and green lines
      ax.plot([], [], color='red', linestyle='solid', label='Battery Used >= 6')
      ax.plot([], [], color='orange', linestyle='dashed', label='Battery Used >= 4')
      ax.plot([], [], color='green', linestyle='dotted', label='Battery Used <= 3')
      ax.plot([], [], color='gray', linestyle='solid', label='Predicted battery %')

      ax.grid(axis='both', color='gray', linestyle='--', linewidth=0.3)
      ax.legend(loc='upper right')  #Display the legend in the top-right corner

      canvas = FigureCanvasTkAgg(f, graphFrame)
      canvas_widget = canvas.get_tk_widget()
      canvas_widget.grid(row=0, column=0, sticky="nswe")

      #Create a new navigation toolbar for zooming and panning
      toolbar = NavigationToolbar2Tk(canvas, graphFrame)

      #Destroy the existing toolbar if it exists
      if 'toolbar' in locals():
         toolbar.grid_forget()

      toolbar.update()
      toolbar.grid(row=1, column=0, sticky="ew")
   
   def dataAnalyse(self):
      self.clearGraphs(False)
      #self.stack.add(self.dataAnalyse)
      battery_info.config(text="")

      chargedCounts = []
      for month in self.months:
         data = conn.execute(f"SELECT * FROM {month} WHERE year='{year}';").fetchall()
         points = [row[0] for row in data]
         chargedCounts.append(self.batteryCharged(points))

      # Create a line plot
      f = plt.Figure(figsize=(16, 6), dpi=75)
      ax = f.add_subplot()
      ax.bar(self.months, chargedCounts,color='b')
      ax.set_xlabel('Month')
      ax.set_ylabel('Charging Count')
      ax.set_title('Battery Charging Count per Month')

      # Add labels on each data point
      for month, count in zip(self.months, chargedCounts):
         ax.annotate(str(count), (month, count), textcoords='offset points', xytext=(0, 5), ha='center', va='bottom')

      ax.grid(axis='both', color='gray', linestyle='--', linewidth=0.3)

      canvas = FigureCanvasTkAgg(f, graphFrame)
      canvas_widget = canvas.get_tk_widget()
      canvas_widget.grid(row=0, column=0, sticky="nswe")

      # Create a new navigation toolbar for zooming and panning
      toolbar = NavigationToolbar2Tk(canvas, graphFrame)

      # Destroy the existing toolbar if it exists
      if 'toolbar' in locals():
         toolbar.grid_forget()

      toolbar.update()
      toolbar.grid(row=1, column=0, sticky="ew")

# Navigation class
class NavigationStack(AppFunctions):
   def __init__(self):
      self.stack = []
      self.current = None

   #Call the function and add it to the stack
   def add(self, function, *args, **kwargs):
      if (function, args, kwargs) not in self.stack:  # Checks if the function is not already inside the stack
         self.stack.append((function, args, kwargs))

         if(len(self.stack) > 1): # if the length of the stack is greater than 1 the button BACK is active
            backB.config(state='active')

      result = function(*args, **kwargs)
      self.current = (function, args, kwargs)

      return result # calls getData(month, day, year) and graph is created

   #call the last called function and pop it from the stack
   def pop_call(self, instance):
      if len(self.stack) < 2: # if the stack doesn't have more than 1 item, then the BACK button should be disabled
         backB.config(state='disabled')

      if not self.is_empty():
         if self.current == self.stack[-1] and len(self.stack) > 1: # It checks if they are equal if yes then it pops the last item
            self.stack.pop()                                        # so the current graph doesn't show twice and it moves to the second last graph

         function, args, kwargs = self.stack.pop()
         self.current = (function, args, kwargs) 

         return function(*args, **kwargs) # calls the function to create a graph
   
   # is_empty returns true if the length of the stack is 0, and false if not
   def is_empty(self) -> bool:
      return len(self.stack) == 0

# UI class
class AppUI: 
   def __init__(self):
      self.appWidth = 1250
      self.appHeight = 750
      self.screen_w = window.winfo_screenwidth()
      self.screen_h = window.winfo_screenheight()

      x = (self.screen_w / 2) - (self.appWidth) + 600
      y = (self.screen_h / 2) - (self.appHeight) + 350 # x and y so the app shows in the center of the screen
      window.geometry(f'{self.appWidth}x{self.appHeight}+{int(x)}+{int(y)}')

      self.func = AppFunctions()
      self.stack = NavigationStack()
      self.main()

   def main(self):
      global errorLabel, graphFrame, battery_info, my_tree, dataFrame, nextB, backB

      sideFrame = Frame(window, relief='sunken', height=self.appHeight, width=350, border=3)
      sideFrame.pack(side=LEFT, fill='y')

      searchFrame = LabelFrame(sideFrame, height=130, width=350, bg=colorPalette().secondaryC, text='Month & Year')
      searchFrame.grid(row=0, column=0, sticky='n')

      dataFrame = LabelFrame(sideFrame, height=600, width=350, bg='#e5e5e5', relief='sunken', border=2, text=f'')
      dataFrame.grid(row=1, column=0)
      
      mainFrame = Frame(window, relief='sunken')
      mainFrame.pack(side=RIGHT, fill='both', expand=True)

      #######################################################################################################################
      #records frame inputs and labels
      
      searchMonth = Entry(searchFrame, highlightthickness=1, border=2, font=('Arial', 9), justify=CENTER)
      searchMonth.grid(row=0, column=0, ipady=5, padx=10, pady=10)

      searchYear = Entry(searchFrame, highlightthickness=1, border=2, font=('Arial', 9), justify=CENTER)
      searchYear.grid(row=0, column=1, ipady=5, padx=10, pady=10)

      button = Button(searchFrame, border=2, text='Search', font=('Arial', 11), relief='groove', bg='#fefae0', cursor="hand2", command=lambda:self.func.searchQuery(searchMonth.get(), searchYear.get())) #self.func.chargedCountsGraph('yearly')
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
         rowheight=30,
         fieldbackground="white"
      )

      my_tree = ttk.Treeview(dataFrame, yscrollcommand=tree_scroll.set)
      my_tree.pack(ipadx=50, ipady=180, fill=BOTH, expand=True)

      tree_scroll.config(command=my_tree.yview)

      my_tree['columns'] = ("Day", "Year")

      my_tree.column("#0", width=0, stretch=NO)
      my_tree.column("Day", anchor=CENTER, width=100)
      my_tree.column("Year", anchor=CENTER, width=120)
      
      my_tree.heading("#0", text='', anchor=W)
      my_tree.heading("Day", text="Day", anchor=CENTER)
      my_tree.heading("Year", text="Year", anchor=CENTER)

      ####################################################################################################
      #side graph and menu frame
      menuBar = Frame(mainFrame, border=1, height=100, bg=colorPalette().accentC)
      menuBar.pack(fill=BOTH, expand=True)

      ###BUTTONS###
      backB = Button(menuBar, text="Back", state="disabled", command=self.func.backButton)
      backB.pack(side="left", padx=5, pady=2)

      homeB = Button(menuBar, text="Home", command=None)
      homeB.pack(side="left", padx=5, pady=2)

      anlData = Button(menuBar, text="Analyse data", command=self.func.dataAnalyse)
      anlData.pack(side="left", padx=5, pady=2)
      ###BUTTONS###

      changeTheme = Button(menuBar, text="theme")
      changeTheme.pack(side="right", padx=5, pady=2)

      graphFrame = Frame(mainFrame, relief='sunken', border=3, height=self.appHeight, bg='#ffffff', width=900)
      graphFrame.pack(fill='both', expand=True)

      bottomInfoFrame = Frame(graphFrame, relief='groove', border=1, height=100, bg='#eaf4f4')
      bottomInfoFrame.grid(row=2, column=0, sticky='nswe')
      
      errorLabel = Label(bottomInfoFrame, text=f'', fg='#e63946')
      errorLabel.pack(side="top", pady=10)

      battery_info = Label(bottomInfoFrame, text=f"", bg='#eaf4f4', fg='#023047', font=('Arial', 10))
      battery_info.pack(side="bottom", pady=15)

      my_tree.bind("<Double-1>", lambda e: self.func.helperFunc(searchMonth.get()))

      # Configure grid rows and columns to expand
      sideFrame.grid_rowconfigure(1, weight=1)  # Make the second row of sideFrame expand
      sideFrame.grid_columnconfigure(0, weight=1)  # Make the first column of sideFrame expand
      dataFrame.grid_rowconfigure(1, weight=1)  # Make dataFrame expand
      
      mainFrame.grid_rowconfigure(0, weight=1)  # Make mainFrame expand vertically
      mainFrame.grid_columnconfigure(0, weight=1)  # Make mainFrame expand horizontally
      graphFrame.grid_rowconfigure(0, weight=1)
      graphFrame.grid_columnconfigure(0, weight=1)

      graphFrame.pack_propagate(False)
      bottomInfoFrame.pack_propagate(False)
      searchFrame.grid_propagate(False)
      dataFrame.grid_propagate(False)
      graphFrame.grid_propagate(False)
   
      #Create graph when the app is started
      self.stack.add(self.func.getData, month, day, year)


AppUI()
window.bind('<Button>', lambda event: event.widget.focus_set())
window.mainloop()
