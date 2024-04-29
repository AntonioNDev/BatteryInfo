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

now = datetime.datetime.now()#current time/date

day = now.strftime("%a %d")
month = now.strftime("%b")
year = now.strftime("%Y")


#NOTE: THE APP is in pre-built so the paths are written like this for now, later 
#there will be another app for instalation and cofiguration

window = Tk()
window.title("Battery Tracker")
window.iconbitmap("logo/logoNBW.ico")
databasePath = 'C:/Users/Antonio/Documents/MyProjects/BatteryInfo/database.db'

# animations is not currently used but it will be future for menu sliding and other animations
class animations:
   def __init__(self) -> None:
      pass

# colorPallete is for the colors of the app
class colorPalette:
   def __init__(self) -> None:
      #default colors
      self.mode = "light"
      self.primaryC = '#eff2ef'
      self.secondaryC = '#C9ADA7'
      self.accentC = '#4f646f'
      self.buttonColor = '#778da9'
      self.buttonColorD = '#84a98c'
      self.disabledButton = "#0b525b"
   
   def lightBG(self):
      #colors for light mode -> default colors
      self.primaryC = '#eff2ef'
      self.secondaryC = '#C9ADA7'
      self.accentC = '#4f646f'
      self.buttonColor = '#778da9'
      self.buttonColorD = '#84a98c'
      self.disabledButton = "#0b525b"
   
   def darkBG(self):
      #colors for dark mode
      ...

# AppFunctions with all methods for the app
class AppFunctions: #TODO: make one function for creating graph so there isn't any duplicate codes
   def __init__(self, navigationStack, colorPalette):
      self.stack = navigationStack
      self.colors = colorPalette
      self.searchON = False
      self.months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

   def switchTheme(self): #TODO: make switch themes option
      if self.colors.mode == "light":
         self.colors.mode = "dark"

         themeButton.config(text="Theme: dark")
         self.colors.darkBG()

      elif self.colors.mode == "dark":
         self.colors.mode = "light"

         themeButton.config(text="Theme: light")
         self.colors.lightBG()

   def backButton(self): #returns to the previus graph
      self.stack.pop_call(self)
   
   def searchButton(self):
      sideFrame.pack(side=LEFT, fill='y')

   def homeButton(self):
      self.stack.add(self.getData, month, day, year)
   
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
   
   def batteryCharged(self, yPoints) -> int: #find a better way to calculate
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
            with sql.connect(databasePath) as conn:
               cursor = conn.cursor()
               data = cursor.execute(f"SELECT * FROM {month} WHERE day=? AND year=?", (day, year)).fetchall()

            for i, x in enumerate(data):
               Ypoints = np.append(Ypoints, [x[0]])

               total_min = x[2]
               hours, minutes = self.minutesToHours(total_min)

               Xpoints = np.append(Xpoints, [f'{hours:02d}:{minutes:02d}']) 

               yDataFAvg.append(x[0])
               xDataFAvg.append(total_min)
               model_data.append((x[2], x[0]))#data for the model

            model_data = np.array(model_data)
            
            self.createGraph(Xpoints, Ypoints, day) #calls the function to create the graph

            if now.strftime("%a %d") == day and len(Xpoints) >= 3: #It works only on the current day, when there are more than 3 xpoints
               threading.Thread(target=self.linear_model, args=(model_data, Xpoints, Ypoints), daemon=True).start()#linear function thread so it doesn't slow down the main thread              

            batteryCharg = self.batteryCharged(Ypoints)#get battery charged count
            averBatt = self.avgBattLife(xDataFAvg, yDataFAvg)# get avg battery

            #Labels for how many times batt was charged and average life of the battery
            battery_info.config(text=f"Average battery: ≈{averBatt[0]}h:{averBatt[1]:.0f}m | Battery charged: {batteryCharg} {"times" if batteryCharg > 1 else "time"}")            
            
            errorLabel.config(text="")#clear errorLabel

         except ValueError:
            errorLabel.config(text=f"We don't have any data for {day}, please try later.")
            
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
            with sql.connect(databasePath) as conn:
               cursor = conn.cursor()
               data = cursor.execute(f"SELECT * FROM {month} WHERE year=?;", (int(year),)).fetchall()

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
   
   def prepare_data(self, data) -> np.ndarray: #prepares the data for the liner regression model
      X = []

      for i in range(0, len(data) - 1):
         target = data[i, 1] - data[i+1, 1]  #Battery percentage change over the interval
         #Exclude differences greater than 13%
         if abs(target) < 12:
            X.append(abs(target))

      #Convert lists to numpy arrays
      X = np.array(X)
      sample_input = X[-2:]

      return sample_input
   
   def linear_model(self, data, x, y):
      try: 
         import joblib
         self.model = joblib.load("C:/Users/Antonio/Documents/MyProjects/BatteryInfo/linearModel/linear_regression_model2024.pkl")
         
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

      f = plt.Figure(figsize=(16, 6), dpi=75)
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
      toolbar.update()
      toolbar.grid(row=1, column=0, sticky="ew")
   
   def dataYearly(self):
      self.clearGraphs(True)
      battery_info.config(text="")
      errorLabel.config(text="")#clear error label

      getYear = searchYear.get()
      chargedCounts = []
      avgChargedCount = 0

      chargedCounts = []
      months = [] #storing only months that have data

      if not getYear:
         getYear = year #if getYear is nullPtr then get the current year.

      try:
         for month in self.months:
            with sql.connect(databasePath) as conn:
               cursor = conn.cursor()
               data = cursor.execute(f"SELECT batteryPerc FROM {month} WHERE year='{getYear}';").fetchall()

            points = [row[0] for row in data]
            
            if points:
               chargedCount = self.batteryCharged(points)
               months.append(month)
               chargedCounts.append(chargedCount)
               avgChargedCount += chargedCount


         avgChargedCount /= len(chargedCounts)

         #Create a line plot
         f = plt.Figure(figsize=(16, 6), dpi=75)
         ax = f.add_subplot()
         
         ax.set_xlabel('Months')
         ax.set_ylabel('Charging Counts')
         ax.set_title(f'Battery Charging Count per Month for {getYear}')
         
         ax.bar(months, chargedCounts, color='b', width=0.4)
         ax.axhline(y=avgChargedCount, color='orange', linestyle='dashed', label=f'Average charged per month: {avgChargedCount:.2f}')
         ax.set_ylim(bottom=0)

         #Add labels on each data point
         for month, count in zip(months, chargedCounts):
            ax.annotate(str(count), (month, count), textcoords='offset points', xytext=(0, 5), ha='center', va='bottom')

         ax.grid(axis='both', color='gray', linestyle='--', linewidth=0.3)
         ax.legend()

         canvas = FigureCanvasTkAgg(f, graphFrame)
         canvas_widget = canvas.get_tk_widget()
         canvas_widget.grid(row=0, column=0, sticky="nswe")

         #Create a new navigation toolbar for zooming and panning
         toolbar = NavigationToolbar2Tk(canvas, graphFrame)
         toolbar.update()
         toolbar.grid(row=1, column=0, sticky="ew")

      except ZeroDivisionError as e:
         errorLabel.config(text=f"We probably don't have any data for that year yet, please try again later. Error: {e}")
   
   def getTotalUsage(self, data):
      """Calculates the total usage time (difference between maximum and minimum levels) for each day."""
      if not data:
         return 0

      min_level = data[0][0]
      max_level = min_level
      total_usage = 0

      for point in data:
         level = point[0]
         min_level = min(min_level, level)
         max_level = max(max_level, level)

         # Only consider full cycles (charge to discharge) for usage calculation
         if level == min_level or point == data[-1]:
            total_usage += max_level - min_level
            min_level = level
            max_level = level

      return total_usage
   
   def dataMonthly(self):
      self.clearGraphs(True)
      errorLabel.config(text="")
      battery_info.config(text="")

      """Creates a line plot showing battery charging activity and calculates averages."""
      fig, (ax1, ax2) = plt.subplots(figsize=(20, 12), dpi=70, nrows=2)
      ax1.grid(axis='both', color='gray', linestyle='--', linewidth=0.3)

      chargedCounts = []
      avgChargedCount = 0
      avgTotalUsage = 0
      days_seen = set()
      getMonth = searchMonth.get()
      getYear = searchYear.get()

      if not getYear and not getMonth:
         getYear = year #if getYear and getMonth are nullPtrs then get the current year and month.
         getMonth = month

      with sql.connect(databasePath) as conn:
         cursor = conn.cursor()
         if getMonth and getYear:
            days = [row[0] for row in cursor.execute(f"SELECT day FROM {getMonth} WHERE year='{getYear}';").fetchall()
                  if (row[0] not in days_seen) and not days_seen.add(row[0])]

      daily_avg_usage = []  #List to store daily average usage
      try:
         for day in days:
            with sql.connect(databasePath) as conn:
               cursor = conn.cursor()

               data = cursor.execute(f"SELECT batteryPerc FROM {getMonth} WHERE day='{day}' AND year='{getYear}';").fetchall()
               points = [row[0] for row in data]
               chargedCount = self.batteryCharged(points)
               totalUsage = self.getTotalUsage(data)

            chargedCounts.append(chargedCount)
            avgChargedCount += chargedCount
            avgTotalUsage += totalUsage

            if chargedCount == 0:
               chargedCount=1

            daily_avg_usage.append(totalUsage/chargedCount)

         avgChargedCount /= len(chargedCounts)
         avgTotalUsage /= len(chargedCounts)

         ax1.set_ylabel("Charged count")
         ax1.set_xticks(range(len(days)))
         ax1.set_xticklabels(days, rotation=35)
         ax1.set_xlabel("Days")
         ax1.set_title(f'Battery count for {getMonth}')

         #Label placeholders
         avgChargedLabel = ax1.plot([], [], color='orange', linestyle='dashed', label=f'AVG charged: {avgChargedCount:.2f}')
         avgUsageLabel = ax2.plot([], [], color='green', linestyle='solid', label=f'AVG total usage: {avgTotalUsage:.2f}')

         ax1.plot(days, chargedCounts, marker='o', linestyle='-', color='b')
         ax1.axhline(y=avgChargedCount, color='orange', linestyle='dashed')  # Average line for charged count
         ax2.axhline(y=avgTotalUsage, color='green', linestyle='solid')  # Average line for total usage

         ax1.plot(days, chargedCounts, marker='o', linestyle='-', color='b')

         #Update label values at the end (avoid flickering)
         avgUsageLabel[0].set_ydata([avgTotalUsage] * len(avgUsageLabel[0].get_xdata()))
         avgChargedLabel[0].set_ydata([avgChargedCount] * len(avgChargedLabel[0].get_xdata()))

         y_offset = 0.04

         #Iterate through each day and count, positioning the text separately
         for day, count in zip(days, chargedCounts):
            #Determine the text position considering the offset
            x_pos = days.index(day)  #Get the x-position based on the day's index
            y_pos = count + y_offset  #Add the offset to the count

            #Add the text to the plot
            ax1.text(x_pos, y_pos, str(count), ha='center', va='bottom',
               color="black", weight="normal")
            
         ax1.legend()  #Display updated legend now

         ax2.set_ylabel("Average usage (minutes)")
         ax2.set_xlabel("Days")
         ax2.set_xticks(range(len(days)))
         ax2.set_xticklabels(days, rotation=35)
         ax2.set_title(f'Average battery usage per day for {getMonth}')
         ax2.bar(days, daily_avg_usage, color='g', label='Avg usage')

         ax2.legend()

         plt.subplots_adjust(hspace=0.5)

         canvas1 = FigureCanvasTkAgg(fig, graphFrame)
         canvas_widget1 = canvas1.get_tk_widget()
         canvas_widget1.grid(row=0, column=0, sticky="nswe")

         #Create a new navigation toolbar for zooming and panning
         toolbar = NavigationToolbar2Tk(canvas1, graphFrame)

         #Destroy the existing toolbar if it exists
         if 'toolbar' in globals():
            toolbar.grid_forget()

         toolbar.update()
         toolbar.grid(row=1, column=0, sticky="ew")
   
      except Exception as e:
         errorLabel.config(text=f'We don\'t have any data for that month or year yet, please try later. {e}')  

      plt.close(fig) #Close the figure to release resources
 
# Navigation class
class NavigationStack(AppFunctions):
   def __init__(self):
      self.stack = []
      self.colors = colorPalette()
      self.current = None

   #Call the function and add it to the stack
   def add(self, function, *args, **kwargs):
      if (function, args, kwargs) not in self.stack:  # Checks if the function is not already inside the stack
         self.stack.append((function, args, kwargs))

      if(len(self.stack) >= 2): # if the length of the stack is greater than 1 the button BACK is active
         backB.config(state='active', bg=f'{self.colors.buttonColor}')

      result = function(*args, **kwargs)
      self.current = (function, args, kwargs)

      return result # calls getData(month, day, year) and graph is created

   #call the last called function and pop it from the stack
   def pop_call(self, instance):
      if len(self.stack) <= 1: # if the stack doesn't have more than 1 item, then the BACK button should be disabled
         backB.config(state='disabled', bg=f'{self.colors.disabledButton}')

      if not self.is_empty():
         if self.current == self.stack[-1] and len(self.stack) > 1: # It checks if they are equal if yes then it pops the last item
            self.stack.pop()                                        # so the current graph doesn't show twice and it moves to the second last graph
            
            function, args, kwargs = self.stack.pop()
            self.current = (function, args, kwargs)

         else:
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

      self.stack = NavigationStack()
      self.colors = colorPalette()
      self.func = AppFunctions(self.stack, self.colors)
      self.main()

   def main(self):
      global errorLabel, menuBar, graphFrame, battery_info, my_tree, dataFrame, nextB, backB, themeButton, yearlyButton, monthlyButton, searchMonth, searchYear, sideFrame

      sideFrame = Frame(window, relief='sunken', height=self.appHeight, width=350, border=3)

      searchFrame = LabelFrame(sideFrame, height=130, width=350, bg=f"{self.colors.primaryC}", text='Month & Year')
      searchFrame.grid(row=0, column=0, sticky='n')

      dataFrame = LabelFrame(sideFrame, height=600, width=350, bg=f'{self.colors.primaryC}', relief='sunken', border=2, text=f'')
      dataFrame.grid(row=1, column=0)
      
      mainFrame = Frame(window, relief='sunken')
      mainFrame.pack(side=RIGHT, fill='both', expand=True)

      #######################################################################################################################
      #records frame inputs and labels
      
      searchMonth = Entry(searchFrame, highlightthickness=1, border=2, font=('Arial', 9), justify=CENTER)
      searchMonth.grid(row=0, column=0, ipady=5, padx=10, pady=10)
      
      searchYear = Entry(searchFrame, highlightthickness=1, border=2, font=('Arial', 9), justify=CENTER)
      searchYear.grid(row=0, column=2, ipady=5, padx=10, pady=10)

      button = Button(searchFrame, border=2, text='Search', font=('Arial', 11), relief='groove', fg='white', bg=f'{self.colors.buttonColor}', cursor="hand2", command=lambda:self.func.searchQuery(searchMonth.get(), searchYear.get())) #self.func.chargedCountsGraph('yearly')
      button.grid(row=1, column=0, pady=3, ipadx=15)
      button.configure(activebackground='white')

      ###########################################Treeview#########################################################
      tree_scroll = Scrollbar(dataFrame)
      tree_scroll.pack(side=RIGHT, fill=Y)

      style = ttk.Style()
      style.theme_use("clam")  
      style.configure("Treeview",
         background=f"{self.colors.primaryC}",
         foreground="#231942",
         rowheight=30,
         fieldbackground=f"{self.colors.primaryC}"
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
      #menues frame
      menuBar = Frame(mainFrame, border=1, height=100, bg=f"{self.colors.primaryC}")
      menuBar.pack(fill=BOTH, expand=True)

      ###BUTTONS###
      searchB = Button(menuBar, text="Search", command=self.func.searchButton, bg=f'{self.colors.buttonColor}', fg="white", cursor="hand2")
      searchB.pack(side="left", padx=5, pady=2)

      backB = Button(menuBar, text="Back", state="disabled", command=self.func.backButton, bg=f'{self.colors.disabledButton}', fg="white", cursor="hand2")
      backB.configure(disabledforeground="white")
      backB.pack(side="left", padx=5, pady=2)

      homeB = Button(menuBar, text="Home", command=self.func.homeButton, bg=f'{self.colors.buttonColor}', fg="white", cursor="hand2")
      homeB.pack(side="left", padx=5, pady=2)

      yearlyButton = Button(menuBar, text="Yearly data", command=lambda: self.stack.add(self.func.dataYearly), bg=f'{self.colors.buttonColorD}', fg="white", cursor="hand2")
      monthlyButton = Button(menuBar, text="Monthly data", command=lambda: self.stack.add(self.func.dataMonthly), bg=f'{self.colors.buttonColorD}', fg="white", cursor="hand2")
      
      themeButton = Button(menuBar, text=f"Theme: {"light"}", bg=f'{self.colors.buttonColor}', fg='white', cursor="hand2", command=self.func.switchTheme)
      themeButton.pack(side="right", padx=5, pady=2)

      yearlyButton.pack(side="left", padx=5, pady=2)
      monthlyButton.pack(side="left", padx=5, pady=2)
      
      ###BUTTONS###
      graphFrame = Frame(mainFrame, relief='sunken', border=3, height=self.appHeight, bg=f"{self.colors.primaryC}", width=900)
      graphFrame.pack(fill='both', expand=True)

      bottomInfoFrame = Frame(graphFrame, relief='groove', border=1, height=100, bg=f'{self.colors.primaryC}')
      bottomInfoFrame.grid(row=2, column=0, sticky='nswe')
      
      errorLabel = Label(bottomInfoFrame, text=f'', fg='#e63946', bg=f'{self.colors.primaryC}')
      errorLabel.pack(side="top", pady=10)

      battery_info = Label(bottomInfoFrame, text=f"", bg=f'{self.colors.primaryC}', fg='#023047', font=('Arial', 10))
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