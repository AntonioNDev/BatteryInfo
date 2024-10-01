""" 


This app creates the database and all the 
configuration for the Battery Tracker app to work 


"""
import os
import shutil

class Settings:
   def __init__(self) -> None:
      self.setup_appdata()

   def setup_appdata(self):
      global app_folder

      appdata_path = os.getenv('APPDATA')
      app_folder = os.path.join(appdata_path, 'BatteryInfo')

      # create the directory if it does not exist
      if not os.path.exists(app_folder):
         os.makedirs(app_folder)
         print("Folder created")

         self.move_files()
         self.create_database()
         self.add_to_startup()

   def add_to_startup(self):
      startup_path = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
      appdata_path = os.getenv('APPDATA')
      battery_info_folder = os.path.join(appdata_path, 'BatteryInfo')

      main_script_path = os.path.join(battery_info_folder, 'main.pyw')

      shutil.copy(main_script_path, startup_path)

      print("moved main.pyw inside the startup")

   def create_database(self):
      import sqlite3 as sql
      
      db_path = os.path.join(app_folder, 'database.db')
      conn = sql.connect(db_path)
      print("database created inside the folder")

   def move_files(self):
      appdata_path = os.getenv('APPDATA')

      destination_folder = os.path.join(appdata_path, 'BatteryInfo')

      folders_to_move = ['logo', 'logs', 'main.pyw', 'linearModel']

      for folder in folders_to_move:
         # Check if the folder exists in the current directory
         if os.path.exists(folder):
            # Construct the destination path for the folder
            dest_path = os.path.join(destination_folder, folder)
            
            if os.path.isdir(folder):
               # Use copytree for directories
               shutil.copytree(folder, dest_path, dirs_exist_ok=True)  # Python 3.8+
               print(f"Copied directory {folder} to {dest_path}")
            else:
               # Use copy for files
               shutil.copy(folder, dest_path)
               print(f"Copied file {folder} to {dest_path}")

         else:
            print(f"{folder} does not exist in the current directory.")

if __name__ == "__main__":
   Settings()
