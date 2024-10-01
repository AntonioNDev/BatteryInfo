from tkinter import ttk
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import sqlite3 as sql

import datetime
import threading
import queue
import gc

matplotlib.use('Agg')

now = datetime.datetime.now() #current time/date

day_ = now.strftime("%a %d")
month_ = now.strftime("%b")
year_ = now.strftime("%Y")

window = ctk.CTk()
window.title("Battery Tracker")


def configure_paths():
   import os

   global databasePath, modelPath

   appdata_path = os.getenv('APPDATA')
   app_folder = os.path.join(appdata_path, 'BatteryInfo')

   databasePath = os.path.join(app_folder, 'database.db')
   logoPath = os.path.join(app_folder, 'logo/logoNBW.ico')
   modelPath = os.path.join(app_folder, 'linearModel/linear_regression_model2024.pkl')

   window.iconbitmap(logoPath)

# colorPallete for the UI
class colorPalette:
   def __init__(self) -> None:
      #default colors
      self.backgroundMainC = '#f6f9f9'
      self.framesC = '#778DA9'

      self.slideSearchC = '#30415F'
      self.slideDataFC = '#334E71'

      self.buttonColorActive = '#92B3DF'
      self.buttonColorDisabled = '#516D91'

      self.selectedTab = ['#a4b3c8', '#f8f7ff']
      self.unselectedTab = ['#72839a', '#f8f7ff']

      self.textC = "#f8f7ff"

      self.errorColor = "#e56b6f"
      self.hoverColor = "#5B9CF0"

      self.borderColor = "#90e0ef"
      self.borderColorDisabled = "#1d3557"

# All the functions the app needs to operate are in the AppFunctions
class AppFunctions: 
   def __init__(self, navigationStack, colorPalette):
      self.stack = navigationStack
      self.colors = colorPalette

      self.taskQueue = queue.Queue()

      self.currentMonth = ''
      self.currentYear = None
      self.months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
   
   def backButton(self): #returns to the previus graph
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
   
   # this function is responsible for the threading
   # processes the given functions in the Queue 
   def process_tasks(self):
      from concurrent.futures import ThreadPoolExecutor

      with ThreadPoolExecutor(max_workers=3) as executor:
         while not self.taskQueue.empty():
            task = self.taskQueue.get()  # Get a task from the queue
            try:
               executor.submit(task)  # Submit the task to a worker
            except Exception as e:
               errorLabel.configure(text=f"{e}")         
            finally:
               self.taskQueue.task_done()  # Mark the task as done
  
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
               data = cursor.execute(f"SELECT batteryPerc, time FROM {month} WHERE day=? AND year=?", (day, year)).fetchall()

            for i in range(len(data)):
               x = data[i]
               Ypoints = np.append(Ypoints, [x[0]])

               total_min = x[1]
               hours, minutes = self.minutesToHours(total_min)

               Xpoints = np.append(Xpoints, [f'{hours:02d}:{minutes:02d}']) 
               
               if i < len(data) - 1: 
                  timeM = abs(data[i][1] - data[i+1][1])
                                 
                  if timeM == 15:
                     yDataFAvg.append(x[0])
                     xDataFAvg.append(total_min)

               model_data.append((x[1], x[0])) #data for the model

            model_data = np.array(model_data)  
            
            if self.currentMonth != month:
               self.dataMonthly()
               self.currentMonth = month
            
            if self.currentYear != year:
               self.dataYearly()
               self.currentYear = year

            self.createGraph(Xpoints, Ypoints, day) #calls the function to create the graph

            if now.strftime("%a %d") == day and len(Xpoints) >= 3: #It works only on the current day, when there are more than 3 xpoints
               self.taskQueue.put(lambda: self.linear_model(model_data, Xpoints, Ypoints))

            threading.Thread(target=self.process_tasks, daemon=True).start()
            
            batteryCharg = self.batteryCharged(Ypoints)#get battery charged count
            averBatt = self.avgBattLife(xDataFAvg, yDataFAvg)# get avg battery
         
            #Labels for how many times batt was charged and average life of the battery
            battery_info.configure(text=f"AVG.battery: ≈{averBatt[0]}h:{averBatt[1]:.0f}m | charged: {batteryCharg} {"times" if batteryCharg > 1 else "time"}")            
            
            errorLabel.configure(text="")#clear errorLabel

         except ValueError:
            errorLabel.configure(text=f"We don't have any data for {day}, please try later.")
            battery_info.configure(text="")
            
      else:
         errorLabel.configure(text="Empty inputs!.")
   
   def helperFunc(self, month):
      try:
         selected = my_tree.focus()
         values = my_tree.item(selected, 'values')
         day = values[0]
         year = values[1]

         self.stack.add(self.getData, month, day, year)
      except Exception as e:
         errorLabel.configure(text=f"{e}")
   
   def searchQuery(self, month, year):
      my_tree.delete(*my_tree.get_children())
      if month and year:
         try:
            with sql.connect(databasePath) as conn:
               cursor = conn.cursor()
               data = cursor.execute(f"SELECT * FROM {month} WHERE year=?;", (int(year),)).fetchall() #BUG: FIX SO THE QUERY ONLY TAKES THE DAY AND THE YEAR, NOT EVERYTHING

            previusDate = ''

            for i, x in enumerate(data):
               if(x[1] != previusDate): #BUG: here in the text... fix it
                  my_tree.insert(parent='', index='end', text='', values=(x[1], x[3]))

               previusDate = x[1]

            errorLabel.configure(text="")

         except Exception as e:
            errorLabel.configure(text=f"{e}")
            
      else:
         errorLabel.configure(text="Empty inputs!.")
   
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
         from joblib import load
         self.model = load(modelPath)
         
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
            x_labels[-1] = 'Predicted BP'  #Set the last label to 'later'
            ax.set_xticks(x)
            ax.set_xticklabels(x_labels, rotation=10)

            ax.scatter([len(x) - 1], [predicted_battery], color='black', s=15, marker='o', linewidth=2, zorder=5)
            ax.annotate(f'{predicted_battery}%', (len(x) - 1, predicted_battery), textcoords='offset points', xytext=(-15, -5), ha='center', fontsize=12, color='black')

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
            ax.annotate('Charged', (x[i], y[i]), textcoords='offset points', xytext=(-30, 0), ha='center', fontsize=12, color='black')

         if y[i] == minimum:
            ax.scatter([x[i]], [y[i]], color='black', s=30, marker='o', linewidth=2, zorder=5)
            ax.annotate(f'Lowest {minimum:.0f}%', (x[i], y[i]), textcoords='offset points', xytext=(-40, 0), ha='center', fontsize=12, color='black')

      ax.set_xticks(range(len(x)))
      ax.set_xticklabels(x, rotation=35)

      ax.set_ylabel("Battery Percentage", fontsize=14)
      ax.set_xlabel("Time", fontsize=14)
      ax.set_title(f'Battery data for {day}', fontsize=14)
      
      # Manually specify the legend entries for red, orange, and green lines
      ax.plot([], [], color='red', linestyle='solid', label='Battery Used >= 6')
      ax.plot([], [], color='orange', linestyle='dashed', label='Battery Used >= 4')
      ax.plot([], [], color='green', linestyle='dotted', label='Battery Used <= 3')
      ax.plot([], [], color='gray', linestyle='solid', label='Predicted battery perc.')
      
      ax.grid(axis='both', color='gray', linestyle='--', linewidth=0.3)
      ax.legend(loc='upper right', fontsize=12)  #Display the legend in the top-right corner

      canvas = FigureCanvasTkAgg(f, frame1_today)
      canvas_widget = canvas.get_tk_widget()
      canvas_widget.grid(row=0, column=0, sticky="nswe")

      #Create a new navigation toolbar for zooming and panning
      toolbar = NavigationToolbar2Tk(canvas, frame1_today, pack_toolbar=False)
      toolbar.update()
      toolbar.grid(row=1, column=0, sticky="ew")
   
   def dataYearly(self):
      self.clearGraphs(True)
      battery_info.configure(text="")
      errorLabel.configure(text="")#clear error label

      getYear = searchYear.get()
      chargedCounts = []
      avgChargedCount = 0

      chargedCounts = []
      months = [] #storing only months that have data

      if not getYear:
         getYear = year_ #if getYear is nullPtr then get the current year.

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

         canvas = FigureCanvasTkAgg(f, frame3_yearly)
         canvas_widget = canvas.get_tk_widget()
         canvas_widget.grid(row=0, column=0, sticky="nswe")

         #Create a new navigation toolbar for zooming and panning
         toolbar = NavigationToolbar2Tk(canvas, frame3_yearly, pack_toolbar=False)
         toolbar.update()
         toolbar.grid(row=1, column=0, sticky="ew")

      except ZeroDivisionError as e:
         errorLabel.configure(text=f"We probably don't have any data for that year yet, please try again later. Error: {e}")
   
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
      errorLabel.configure(text="")
      battery_info.configure(text="")

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
         getYear = year_ #if getYear and getMonth are nullPtrs then get the current year and month.
         getMonth = month_

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
            
         ax2.set_ylabel("Average usage (minutes)")
         ax2.set_xlabel("Days")
         ax2.set_xticks(range(len(days)))
         ax2.set_xticklabels(days, rotation=35)
         ax2.set_title(f'Average battery usage per day for {getMonth}')
         ax2.bar(days, daily_avg_usage, color='g', label='Avg usage')

         ax1.legend()  #Display updated legends now
         ax2.legend()

         plt.subplots_adjust(hspace=0.5)

         canvas1 = FigureCanvasTkAgg(fig, frame2_monthly)
         canvas_widget1 = canvas1.get_tk_widget()
         canvas_widget1.grid(row=0, column=0, sticky="nswe")

         #Create a new navigation toolbar for zooming and panning
         toolbar = NavigationToolbar2Tk(canvas1, frame2_monthly, pack_toolbar=False)

         #Destroy the existing toolbar if it exists
         if 'toolbar' in globals():
            toolbar.grid_forget()

         toolbar.update()
         toolbar.grid(row=1, column=0, sticky="ew")
   
      except Exception as e:
         errorLabel.configure(text=f'We don\'t have any data for that month or year yet, please try later. {e}')  

      plt.close(fig) #Close the figure to release resources

# Navigation class
class NavigationStack(AppFunctions):
   def __init__(self):
      self.stack = []
      self.stackForward = []
      self.colors = colorPalette()
      self.current = None

   #Call the function and add it to the stack
   def add(self, function, *args, **kwargs):
      if (function, args, kwargs) not in self.stack:  # Checks if the function is not already inside the stack
         self.stack.append((function, args, kwargs))

      if(len(self.stack) >= 2): # if the length of the stack is greater or equal to 2 the button BACK is active
         backward_button.configure(state='active', fg_color=f"{self.colors.buttonColorActive}", border_color=f'{self.colors.borderColor}')

      result = function(*args, **kwargs)
      self.current = (function, args, kwargs)

      return result # calls getData(month, day, year) and graph is created

   #call the last called function and pop it from the stack
   def pop_call(self, instance):
      if len(self.stack) <= 2: # if the stack doesn't have more or 2 items, then the BACK button should be disabled
         backward_button.configure(state='disabled', fg_color=f"{self.colors.buttonColorDisabled}", border_color=f'{self.colors.borderColorDisabled}')

      if not self.is_empty() and len(self.stack) >= 2:
         if self.current == self.stack[-1]: # It checks if they are equal if yes then it pops the last item
            self.stackForward.append(self.stack.pop())             # so the current graph doesn't show twice and it moves to the second last graph
            
            function, args, kwargs = self.stack[-1]
            self.current = (function, args, kwargs)

         else:
            function, args, kwargs = self.stack.pop()
            self.current = (function, args, kwargs) 

         return function(*args, **kwargs) # calls the function to create a graph
      
   # is_empty returns true if the length of the stack is 0, and false if not
   def is_empty(self) -> bool:
      return len(self.stack) == 0

# animated slied panel
class SlidePanel(ctk.CTkFrame):
   def __init__(self, parent, start_pos, end_pos, months, functions):
      super().__init__(master = parent, corner_radius=5, fg_color='#415A77', border_width=2, border_color='#1D3049')

      self.years = ["2023", "2024"]

      self.start_pos = start_pos
      self.end_pos = end_pos
      self.width = abs(start_pos - end_pos) - 0.05

      self.pos = self.start_pos #-0.3
      self.in_start_pos = True

      #layout
      self.colors = colorPalette()
      self.months = months
      self.func = functions
      self.place(relx = self.start_pos, rely = 0.09, relwidth = self.width, relheight = 0.9)

   def animate(self):
      if not self.in_start_pos:
         self.animate_forward()
      else:
         self.animate_backwards()
   
   def animate_forward(self):
      if self.pos > self.start_pos:
         self.pos -= 0.055
         self.place(relx = self.pos, rely = 0.09, relwidth = self.width, relheight = 0.9)
         self.after(25, self.animate_forward)
      else:
         self.in_start_pos = True

   def animate_backwards(self):
      if self.pos < self.end_pos:
         self.pos += 0.055
         self.place(relx = self.pos, rely = 0.09, relwidth = self.width, relheight = 0.9)
         self.after(25, self.animate_backwards)
      else:
         self.in_start_pos = False

   # layout for the side frame (treeview and other components)
   def layout(self):
      global my_tree, dataFrame, searchYear, searchMonth

      # Make sideFrame responsive
      sideFrame.grid_rowconfigure(0, weight=0)  # Search frame row doesn't expand
      sideFrame.grid_rowconfigure(1, weight=1)  # Data frame row expands
      sideFrame.grid_columnconfigure(0, weight=1)  # Make first column of sideFrame expandable

      #Search Frame
      searchFrame = ctk.CTkFrame(sideFrame, height=130, width=350, fg_color=f'{self.colors.slideSearchC}')
      searchFrame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)  # Expand the frame to fill available space
      searchFrame.grid_propagate(False)  # Prevent the frame from resizing based on its children

      #Data Frame
      dataFrame = ctk.CTkFrame(sideFrame, height=550, width=300)
      dataFrame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)  # Expand the frame to fill available space
      dataFrame.grid_propagate(False)  # Prevent the frame from resizing based on its children
      dataFrame.grid_rowconfigure(0, weight=1)  # Make the Treeview inside dataFrame expand
      dataFrame.grid_columnconfigure(0, weight=1)  # Expand Treeview horizontally in dataFrame

      #Search Frame Components
      searchMonth = ctk.CTkComboBox(searchFrame, font=('Arial', 12), justify="center", values=self.months, corner_radius=10)
      searchMonth.grid(row=0, column=0, ipady=5, padx=5, pady=10, sticky='ew')
      searchMonth.set(month_)

      searchYear = ctk.CTkComboBox(searchFrame, font=('Arial', 12), justify="center", values=self.years, corner_radius=10)
      searchYear.grid(row=0, column=1, ipady=5, padx=5, pady=10, sticky='ew')
      searchYear.set(year_)

      button = ctk.CTkButton(searchFrame, text='Search', font=('Arial', 14), corner_radius=7, fg_color=f'{self.colors.buttonColorActive}',
                             text_color=f'{self.colors.textC}', hover_color=f'{self.colors.hoverColor}', 
                             command=lambda: self.func.searchQuery(searchMonth.get(), searchYear.get()), 
                             border_width=2, border_color=f'{self.colors.borderColor}', 
                             width=110)
      
      button.grid(row=1, column=0, columnspan=2, pady=2, padx=10, sticky='ns') 

      # Make the columns in searchFrame responsive
      searchFrame.grid_columnconfigure(0, weight=1)
      searchFrame.grid_columnconfigure(1, weight=1)

      # Treeview with Scrollbar
      tree_scroll = ctk.CTkScrollbar(dataFrame)
      tree_scroll.grid(row=0, column=1, sticky='ns')  # Attach to the right of the Treeview

      style = ttk.Style()
      style.theme_use("clam")
      style.configure("Treeview",
         background=f"{self.colors.slideDataFC}",
         foreground=f"{self.colors.textC}",
         rowheight=35,
         font=('Arial', 12), 
         fieldbackground=f"{self.colors.slideDataFC}"
      )

      my_tree = ttk.Treeview(dataFrame, yscrollcommand=tree_scroll.set)
      my_tree.grid(row=0, column=0, sticky='nsew')  # Make the Treeview fill and expand

      tree_scroll.configure(command=my_tree.yview)

      # Define columns for the Treeview
      my_tree['columns'] = ("Day", "Year")
      my_tree.column("#0", width=0, stretch=False)
      my_tree.column("Day", anchor="center", width=100)
      my_tree.column("Year", anchor="center", width=120)

      my_tree.heading("#0", text='', anchor="w")
      my_tree.heading("Day", text="Day", anchor="center")
      my_tree.heading("Year", text="Year", anchor="center")
      style.configure("Treeview.Heading", font=('Arial', 13))

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
   
   def data_frame(self):
      global errorLabel, frame1_today, frame2_monthly, frame3_yearly, battery_info

      # Create ttk.Notebook with 2 frames inside
      notebook = ttk.Notebook(mainFrame)
      notebook.grid(row=1, column=0, padx=10, pady=5, sticky='nsew', ipadx=5, ipady=5)  # Expand to fill x and y axis
      mainFrame.grid_rowconfigure(1, weight=5)  # 80% of space for the notebook
      mainFrame.grid_columnconfigure(0, weight=1)  # Make notebook fill width

      # Create the frames to add to the notebook
      frame1_today = ttk.Frame(notebook)
      frame2_monthly = ttk.Frame(notebook)
      frame3_yearly = ttk.Frame(notebook)

      # Add frames to the notebook     
      notebook.add(frame1_today, text="Home")
      notebook.add(frame2_monthly, text="Monthly data graph")
      notebook.add(frame3_yearly, text="Yearly data graph")

      notebook.select(frame1_today)

      #Error label will display the bugs/exceptions
      errorLabel = ctk.CTkLabel(mainFrame, text="", text_color=f"{self.colors.errorColor}")
      errorLabel.grid(row=2, column=0, sticky='ns')

      #Battery info with the average battery life and charged count will be displayed here
      battery_info = ctk.CTkLabel(mainFrame, text="", text_color="#353535")
      battery_info.grid(row=3, column=0, sticky='ns')

      #preLoad labels for the tabs:
      preLoad = ctk.CTkLabel(frame1_today, text='Here the graph will be loaded!.', font=('Arial', 13), text_color="gray").grid(row=0, column=0, sticky="nsew")
      preLoad = ctk.CTkLabel(frame2_monthly, text='Here the graph will be loaded!.', font=('Arial', 13), text_color="gray").grid(row=0, column=0, sticky="nsew")
      preLoad = ctk.CTkLabel(frame3_yearly, text='Here the graph will be loaded!.', font=('Arial', 13), text_color="gray").grid(row=0, column=0, sticky="nsew")

      # Configure tab style
      style = ttk.Style()
      style.configure("TNotebook", tabposition='n')
      style.configure("TNotebook.Tab", font=('Arial', 12))
      style.configure('TNotebook', background=f'{self.colors.backgroundMainC}')
      style.configure('TNotebook.Tab', padding=[5, 5])

      # Change the active tab background color (selected tab)
      style.map('TNotebook.Tab', 
         background=[('selected', f'{self.colors.selectedTab[0]}')],  # Active tab background
         foreground=[('selected', f'{self.colors.selectedTab[1]}')],  # Active tab text color
      )

      # Set the background for inactive tabs
      style.configure('TNotebook.Tab', background=f'{self.colors.unselectedTab[0]}', foreground=f'{self.colors.unselectedTab[1]}')

      #remove the focus around the box when clicked
      style.layout('TNotebook.Tab', [
            ('Notebook.tab', {
                  'sticky': 'nswe', 
                  'children': [
                     ('Notebook.padding', {
                        'side': 'top',
                        'children': [
                              ('Notebook.label', {'sticky': ''})
                        ]
                     })
                  ]
            })
         ])

      # Configure frame sizes (90% height)
      mainFrame.grid_rowconfigure(1, weight=9)  # 90% for the notebook
      mainFrame.grid_rowconfigure(2, weight=1)  # 10% below notebook for something else

      # Make sure labels are centered and frames are responsive
      frame1_today.grid_rowconfigure(0, weight=1)
      frame1_today.grid_columnconfigure(0, weight=1)
      frame2_monthly.grid_rowconfigure(0, weight=1)
      frame2_monthly.grid_columnconfigure(0, weight=1)
      frame3_yearly.grid_rowconfigure(0, weight=1)
      frame3_yearly.grid_columnconfigure(0, weight=1)
   
   def nav_frame(self):
      global backward_button, navBar, forward_button

      navBar = ctk.CTkFrame(mainFrame, height=45, corner_radius=10, fg_color=f"{self.colors.framesC}", border_width=2, border_color='#88A3C7')
      navBar.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)  # Expand along x-axis
      mainFrame.grid_rowconfigure(0, weight=0)  # Keep navbar fixed at the top
      mainFrame.grid_columnconfigure(0, weight=2)  # Ensure it expands horizontally

      #Create Search button on the top left
      search_button = ctk.CTkButton(navBar, text="Search", width=80, height=30, 
                                    command=sideFrame.animate, fg_color=f"{self.colors.buttonColorActive}", hover_color=f'{self.colors.hoverColor}', 
                                    font=('Arial', 14), text_color=f'{self.colors.textC}', border_width=2, border_color=f'{self.colors.borderColor}')
      search_button.grid(row=0, column=0, padx=10, pady=10)

      #Create Forward and Backward buttons
      backward_button = ctk.CTkButton(navBar, text="<-", width=30, 
                                      height=30, cursor="hand2", state="disabled", command=self.func.backButton, fg_color=f"{self.colors.buttonColorDisabled}", border_width=2, border_color=f'{self.colors.borderColorDisabled}')
      backward_button.grid(row=0, column=1, padx=5)

      forward_button = ctk.CTkButton(navBar, text="->", width=30, height=30, 
                                     cursor="hand2", state="disabled", command=self.func, fg_color=f"{self.colors.buttonColorDisabled}", border_width=2, border_color=f'{self.colors.borderColorDisabled}')
      forward_button.grid(row=0, column=2, padx=5)
   
      # notebook expands with the window resize
      navBar.grid_columnconfigure(3, weight=1)  
   
   def main(self):
      global mainFrame, sideFrame

      mainFrame = ctk.CTkFrame(window, fg_color=f"{self.colors.backgroundMainC}")
      mainFrame.pack(anchor="center", fill="both", expand=True)

      sideFrame = SlidePanel(mainFrame, -0.3, 0, self.func.months, self.func)
      sideFrame.layout()

      self.nav_frame()
      self.data_frame()

      sideFrame.lift()

      my_tree.bind("<Double-1>", lambda e: self.func.helperFunc(searchMonth.get()))
      self.func.taskQueue.put(lambda: self.stack.add(self.func.getData, month_, day_, year_))
      threading.Thread(target=self.func.process_tasks, daemon=True).start()

if __name__ == "__main__":
   configure_paths()
   AppUI()
   window.bind('<Button>', lambda event: event.widget.focus_set())
   window.mainloop()
