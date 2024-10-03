import sqlite3
import numpy as np
from sklearn.linear_model import LinearRegression
import joblib
import datetime
import os

class Model:
    def __init__(self) -> None:
        self.X = []  # Features (battery percentage differences)
        self.Y = []  # Target (battery percentage change for future time interval)
        
        # Define the time intervals for prediction (e.g., 30 minutes aka. 2x15 (one interval is 15 minutes))
        # so it takes the last 2 intervals
        self.prediction_interval = 2
        self.months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'] #months 

        self.now = datetime.datetime.now()

        self.day = self.now.strftime("%a %d")
        self.month = self.now.strftime("%b")
        self.year = self.now.strftime("%Y")

        self.configure_paths()
        self.main()

    def configure_paths(self):
        global db_path, logsPath, conn, cur, settingsPath, modelPath

        # Connect to the database
        appdata_path = os.getenv('APPDATA')
        app_folder = os.path.join(appdata_path, 'BatteryInfo')

        db_path = os.path.join(app_folder, 'database.db')
        logsPath = os.path.join(app_folder, 'logs')
        settingsPath = os.path.join(app_folder, 'linearModel/settings.json')
        modelPath = os.path.join(app_folder, f'linearModel/linear_regression_model{self.year}.pkl')

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

    def prepare_data(self):
        # Iterate over the database data and calculate differences
        for month in self.months:
            cur.execute(f"SELECT time, batteryPerc FROM {month} WHERE year='{self.year}';")
            data = cur.fetchall()
            data = np.array(data)
            
            # Calculate battery percentage differences for the chosen interval
            for i in range(len(data) - self.prediction_interval):
                features = data[i:i+self.prediction_interval, 1]  # Battery percentage values
                target = data[i+self.prediction_interval, 1] - data[i, 1]  # Battery percentage change over the interval
                
                # Exclude differences greater than or equal to 10%
                if abs(target) < 10:
                    self.X.append(features)
                    self.Y.append(target)

        # Find the maximum length among X and Y
        max_length = max(len(self.X), len(self.Y))

        # Pad X and Y with zeros to make them the same length
        self.X = np.pad(self.X, ((0, max_length - len(self.X)), (0, 0)), mode='constant')
        self.Y = np.pad(self.Y, (0, max_length - len(self.Y)), mode='constant')

        # Convert lists to numpy arrays
        self.X = np.array(self.X)
        self.Y = np.array(self.Y)

    def save_model(self):
        model = LinearRegression() # Create and train the Linear Regression model
        model.fit(self.X, self.Y)

        joblib.dump(model, f'{modelPath}') # Save the trained model to a file

    def update_version(self):
        import json
        from datetime import datetime
        
        # Load the JSON file
        with open(f'{settingsPath}', 'r') as txt:
            data = json.load(txt)
        
        # Increment the version by 1
        version = data.get('version', '0.0')
        major, minor = map(int, version.split('.'))
        new_version = f"{major + 1}.{minor}"
        data['version'] = new_version

        # Set the current date (day.month.year)
        current_date = datetime.now().strftime('%d.%m.%Y')
        data['last_updated_date'] = current_date

        # Save the changes back to the file
        with open(f'{settingsPath}', 'w') as txt:
            json.dump(data, txt, indent=4)

    def main(self):
        import logging 

        logging.basicConfig(filename=f'{logsPath}/errorLogs.log', level=logging.ERROR, format='%(levelname)s-%(message)s')

        try:
            self.prepare_data()
            self.save_model()
        except Exception as e:
            logging.error(f'{self.day}: {e}')
        finally:
            self.update_version()

if __name__ == '__main__':
    Model()