""" 


This app creates the database and all the 
configuration for the Battery Tracker app to work 


"""
import os
import shutil

from tkinter import ttk
import customtkinter as ctk

window = ctk.CTk()
window.title("Configuration")

class Settings:
   def setup_appdata(self):
      global app_folder

      appdata_path = os.getenv('APPDATA')
      app_folder = os.path.join(appdata_path, 'BatteryInfo')

      # create the directory if it does not exist
      if not os.path.exists(app_folder):
         os.makedirs(app_folder)
         label = ctk.CTkLabel(labelsFrame, text=f"Directory created inside: {app_folder}", font=('Arial', 10)).pack(padx=5, pady=5, anchor="w")

         self.create_database()
         self.move_files()
         self.add_to_startup()

   def add_to_startup(self):
      startup_path = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
      appdata_path = os.getenv('APPDATA')
      battery_info_folder = os.path.join(appdata_path, 'BatteryInfo')

      main_script_path = os.path.join(battery_info_folder, 'main.pyw')

      shutil.copy(main_script_path, startup_path)

      label = ctk.CTkLabel(labelsFrame, text=f"main.pyw moved to startup folder: {main_script_path}", font=('Arial', 11)).pack(padx=5, pady=5, anchor="w")

   def create_database(self):
      import sqlite3 as sql
      
      db_path = os.path.join(app_folder, 'database.db')
      conn = sql.connect(db_path)
      label = ctk.CTkLabel(labelsFrame, text=f"database created inside: {db_path}", font=('Arial', 11)).pack(padx=5, pady=5, anchor="w")

   def move_files(self):
      appdata_path = os.getenv('APPDATA')
      destination_folder = os.path.join(appdata_path, 'BatteryInfo')
      folders_to_move = ['logo', 'logs', 'linearModel', 'testDatabase', 'main.pyw']

      for folder in folders_to_move:
         # Check if the folder exists in the current directory
         if os.path.exists(folder):
            # Construct the destination path for the folder
            dest_path = os.path.join(destination_folder, folder)
            
            if os.path.isdir(folder):
               # Use copytree for directories
               shutil.copytree(folder, dest_path, dirs_exist_ok=True)
               label = ctk.CTkLabel(labelsFrame, text=f"Directory {folder} copied inside: {dest_path}", font=('Arial', 11)).pack(padx=5, pady=5, anchor="w")

            else:
               # Use copy for files
               shutil.copy(folder, dest_path)
               label = ctk.CTkLabel(labelsFrame, text=f"File {folder} copied inside: {dest_path}", font=('Arial', 11)).pack(padx=5, pady=5, anchor="w")

         else:
            label = ctk.CTkLabel(labelsFrame, text=f"{folder} does not exist", font=('Arial', 11)).pack(padx=5, pady=5, anchor="w")

   def clear_labels(self):
      for widget in labelsFrame.winfo_children(): # Clear labels
         widget.destroy()

class confUI:
   def __init__(self) -> None:
      self.appWidth = 700
      self.appHeight = 350
      self.screen_w = window.winfo_screenwidth()
      self.screen_h = window.winfo_screenheight()

      x = (self.screen_w / 2) - (self.appWidth) + (self.appWidth/1.5)
      y = (self.screen_h / 2) - (self.appHeight) + (self.appHeight/1.5) # x and y so the app shows in the center of the screen
      window.geometry(f'{self.appWidth}x{self.appHeight}+{int(x)}+{int(y)}')

      self.settings = Settings()

      self.main()

   def start_process(self):
      import threading

      def thread_target():
         self.settings.clear_labels()
         self.settings.setup_appdata()
         configureButton.configure(state="normal")  # Re-enable the button after the process finishes

      # Start the background thread
      x = threading.Thread(target=thread_target, daemon=True).start()
      configureButton.configure(state="disabled")  # Disable the button while the process runs

   def nav_frame(self):
      global navBar, configureButton

      navBar = ctk.CTkFrame(mainFrame, height=45, corner_radius=10, fg_color=f"#778DA9", border_width=2, border_color='#88A3C7')
      navBar.grid(row=0, column=0, sticky='nsew', padx=10, pady=5)  # Expand along x-axis

      mainFrame.grid_rowconfigure(0, weight=0)  # Keep navbar fixed at the top
      mainFrame.grid_columnconfigure(0, weight=2)  # Ensure it expands horizontally

      # Create Search button on the top left
      configureButton = ctk.CTkButton(navBar, text="Configure", width=80, height=30, 
                                    command=self.start_process, fg_color=f"#92B3DF", hover_color=f'#5B9CF0', 
                                    font=('Arial', 14), text_color=f'#f8f7ff', border_width=2, border_color=f'#90e0ef')
      configureButton.grid(row=0, column=0, padx=10, pady=10)

      # notebook expands with the window resize
      navBar.grid_columnconfigure(3, weight=1) 

   def information_frame(self):
      global labelsFrame

      labelsFrame = ctk.CTkFrame(mainFrame, fg_color='#dedbd2', border_color=f"#90e0ef", border_width=2)
      labelsFrame.grid(row=1, column=0, sticky="nswe", padx=10, pady=10, ipady=5, ipadx=10)

      mainFrame.grid_rowconfigure(1, weight=9)  # 80% of space for the notebook
      mainFrame.grid_columnconfigure(0, weight=1)

   def main(self):
      global mainFrame

      mainFrame = ctk.CTkFrame(window, fg_color=f"#f6f9f9")
      mainFrame.pack(anchor="center", fill="both", expand=True)

      self.nav_frame()
      self.information_frame()

if __name__ == "__main__":
   confUI()
   window.bind('<Button>', lambda event: event.widget.focus_set())
   window.resizable(False, False)
   window.mainloop()


