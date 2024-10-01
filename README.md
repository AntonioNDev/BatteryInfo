<h1 align="center">Battery Tracking App</h1>
<hr>
<h3 align="center">Short explanation how the app works</h3>
<p align="center">This app is designed to monitor the battery percentage of your device. It saves your percentage every 15 minutes in a database. The main work for storing the data is done by the main.pyw file. Additionally, there is a BatteryTracker.py file where you can view your data through graphs for any day that has been saved in the database.</p>
<hr>
<h3 align="center">What you need to install</h3>
<p>The app to work properly firstly you need to write this:</p>
<p><strong>pip3 install --upgrade -r requirements.txt</strong></p>

<h3 align="center">Usage Instructions</h3>
<ol>
<li>Ensure you have Python 3.11 or higher installed by running:</li>
<p><strong>python --version</strong></p>

<li>After fetching the code, open the <strong>configure.py</strong> file. This will:</li>
<ul>
<li>Move <strong>main.pyw</strong> to the startup folder, allowing the app to run in the background every time the laptop starts.</li>
<li>The app collects the battery percentage every 15 minutes and stores the data in a local database.</li>
<li>Logs and other necessary folders are moved inside the app folder located in <strong>%appdata%</strong>.</li>
</ul>

<li>The <strong>BatteryTracker.py</strong> can be run from any location on your computer as it will automatically access the database and log files in <strong>%appdata%</strong>.</li>

<li><strong>Optional</strong>: If you'd like, you can compile <strong>BatteryTracker.py</strong> into an executable using pyinstaller:</li>
<p><strong>pyinstaller --onefile BatteryTracker.py</strong></p>
<p>But this step is not necessary for the app to function.</p>

<li>The app includes a linear regression model to predict future battery usage. This model updates every month based on the collected data.</li>
</ol>

<h3 align="center">Important Notes</h3>
<ul>
<li>Do not delete any folders or files located in <strong>%appdata%</strong>, as this will cause the app to crash.</li>
<li>There is a <strong>testDatabase</strong> folder included if you wish to see how the app works with a sample database. If you want to check, open the BatteryTracker.py and change the location of the database to be the testDatabase</li>
</ul>

<h3 align="center">Feedback</h3>
<p>If you find any bugs or have suggestions, feel free to fork the repository or send your ideas. Thanks!</p>

<hr>
<img src="appImg/appImage.png" alt="App Image" align="center">
