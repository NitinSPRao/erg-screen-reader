import csv
import sys
import subprocess
from datetime import datetime


result = subprocess.run(['python3','FitToCSV.py',sys.argv[1], ], capture_output=True, text=True)

data_field = sys.argv[2]

def highest_avg(n, value_list):
  max_n = 0
  for i in range(1, n+1):
    max_n += value_list[i]
  curr_n = max_n
  for i in range(n+1, len(value_list)):
    curr_n = curr_n - value_list[i - n+1] + value_list[i]
    max_n = max(curr_n,max_n)

  return max_n/n


def find_max(value_list):
  max_n = 0;
  for i in value_list:
    max_n = max(i, max_n)

  return max_n

def calculate_speed(distance1, distance2, time1, time2):
    distance_delta = distance2 - distance1
    time_delta = (time2 - time1).total_seconds() / 3600
    if time_delta == 0:
        return 0
    return distance_delta / time_delta


def convert_speed_to_pace(speed):
    if speed == 0:
        return float('inf')
    speed_mph = speed / 1609.34
    pace_min_per_mile = 60 / speed_mph
    return pace_min_per_mile


def find_time(time_1, time_2):
    time_format = "%Y-%m-%d %H:%M:%S"
    datetime1 = datetime.strptime(time_1, time_format)
    datetime2 = datetime.strptime(time_2, time_format)

    difference = datetime2 - datetime1

    seconds = difference.total_seconds()


    hour = seconds // 3600
    seconds %= 3600
    minute = seconds // 60
    seconds %= 60

    formatted_output = "%02d:%02d:%02d" % (hour, minute, seconds)
    return formatted_output


csv_file = sys.argv[1][:-3] + "csv"
with open(csv_file, 'r') as fit_csv:
    reader = csv.reader(fit_csv)
    headers = next(reader)
    time_index = headers.index("timestamp")
    distance_index = headers.index("distance") if data_field == "pace" else None
    try:
        seek_value = headers.index(data_field) if data_field != "pace" else None
    except ValueError:
        print(f"Data field '{data_field}' not found in the CSV file.")
        subprocess.run(["rm", csv_file], shell=True)
        sys.exit(1)

    value_list = []
    paces = []  # List to store pace values if data_field is "pace"
    prev_time = prev_distance = None

    for row in reader:
        if data_field == "pace":
            if row[time_index]:  # Check if the timestamp is not empty
                current_time = datetime.strptime(row[time_index], "%Y-%m-%d %H:%M:%S")
                current_distance = float(row[distance_index])

                if prev_time is not None and prev_distance is not None:
                    speed = calculate_speed(prev_distance, current_distance, prev_time, current_time)
                    pace = convert_speed_to_pace(speed)
                    if pace != float('inf'):
                      paces.append(pace)

                prev_time = current_time
                prev_distance = current_distance
        else:
            try:
                value = float(row[seek_value])
                value_list.append(value)
            except ValueError:
                pass

#subprocess.run(["rm", csv_file], shell=True)

# Handle the calculation based on the data field
if data_field == "pace":
    # Process paces list
    if paces:
        avg_pace = sum(paces) / len(paces)
        max_pace = min(paces)

        print(f"Average Pace: {avg_pace:.2f} min/mile")
        print(f"Fastest Pace: {max_pace:.2f} min/mile")

else:
    cum_value = sum(value_list)
    num_values = len(value_list)
    if num_values > 0:
        avg_value = cum_value / num_values
        max_value = find_max(value_list)
    else:
        avg_value = max_value = 0

    print("avg %s: %d\nmax %s: %d" % (data_field, avg_value, data_field, max_value))
    print("best 1 min: %d\nbest %s min: %d" % (highest_avg(60, value_list), sys.argv[3], highest_avg(int(sys.argv[3]) * 60, value_list)))
