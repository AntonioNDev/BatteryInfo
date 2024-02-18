import sqlite3 as sql
import matplotlib.pyplot as plt

# Connect to the database
databasePath = 'C:/Users/Antonio/Documents/MyProjects/BatteryInfo/database.db'
conn = sql.connect(databasePath)
cur = conn.cursor()

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def batteryCharged(yPoints):
    """Calculates the number of times the battery was charged based on consecutive increases in battery level."""
    if len(yPoints) < 2:
        return 0

    batteryChargedCount = 0
    for current, next_ in zip(yPoints, yPoints[1:]):
        if next_ > current:
            batteryChargedCount += 1

    return batteryChargedCount


def getTotalUsage(data):
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


def monthly(month):
    """Creates a line plot showing battery charging activity and calculates averages."""
    fig, (ax1, ax2) = plt.subplots(figsize=(20, 8), dpi=70, nrows=2)
    ax1.grid(axis='both', color='gray', linestyle='--', linewidth=0.3)

    chargedCounts = []
    avgChargedCount = 0
    avgTotalUsage = 0
    days_seen = set()
    days = [row[1] for row in conn.execute(f"SELECT * FROM {month} WHERE year='2024';").fetchall()
           if (row[1] not in days_seen) and not days_seen.add(row[1])]

    daily_avg_usage = []  # List to store daily average usage
    for day in days:
        data = conn.execute(f"SELECT * FROM {month} WHERE day='{day}' AND year='2024';").fetchall()
        points = [row[0] for row in data]
        chargedCount = batteryCharged(points)
        totalUsage = getTotalUsage(data)

        chargedCounts.append(chargedCount)
        avgChargedCount += chargedCount
        avgTotalUsage += totalUsage

        if chargedCount == 0:
            chargedCount=1

        daily_avg_usage.append(totalUsage/chargedCount)


    avgChargedCount /= len(chargedCounts)
    avgTotalUsage /= len(chargedCounts)

    ax1.set_ylabel("Charged count")
    ax1.set_xlabel("Days")
    ax1.set_title(f'Battery count for {month}')

    # Label placeholders to be updated later
    avgChargedLabel = ax1.plot([], [], color='orange', linestyle='dashed', label=f'AVG charged: {avgChargedCount:.2f}')
    avgUsageLabel = ax2.plot([], [], color='green', linestyle='solid', label=f'AVG total usage: {avgTotalUsage:.2f}')

    ax1.plot(days, chargedCounts, marker='o', linestyle='-', color='b')

    # Update label values at the end (avoid flickering)
    avgUsageLabel[0].set_ydata([avgTotalUsage] * len(avgUsageLabel[0].get_xdata()))
    avgChargedLabel[0].set_ydata([avgChargedCount] * len(avgChargedLabel[0].get_xdata()))

    y_offset = 0.05

    # Iterate through each day and count, positioning the text separately
    for day, count in zip(days, chargedCounts):
        # Determine the text position considering the offset
        x_pos = days.index(day)  # Get the x-position based on the day's index
        y_pos = count + y_offset  # Add the offset to the count

        # Customize the text element's appearance (if desired)
        text_color = 'black'  # Example customization
        font_weight = 'bold'  # Example customization

        # Add the text to the plot
        ax1.text(x_pos, y_pos, str(count), ha='center', va='bottom',
            color=text_color, weight=font_weight)
        
    ax1.legend()  # Display updated legend now

    ax2.set_ylabel("Average usage (minutes)")
    ax2.set_xlabel("Days")
    ax2.set_title(f'Average battery usage per day for {month}')
    ax2.bar(days, daily_avg_usage, color='g', label='Avg usage')

    ax2.legend()

    plt.show()

# Call the monthly function for desired month
monthly("Feb")
