import csv
from os import startfile, stat
import time
import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import numpy as np
from dateutil.parser import parse
import matplotlib.pyplot as plt
import glob
import json

if __name__ == "__main__":
    with open("gps.csv", 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)
        old_trip_id = "1a805fed-4941-5b94-aa56-09e70beb54c7"
        old_device_id = 50109695
        new_trip_id = ""
        json_array = []
        path_array = []
        tstamp_array = []
        for row in csvreader:
            if len(row) == 0:
                continue
            if row[0] == '':
                continue
            temp_dt = datetime.datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S')
            timestamp = int(temp_dt.timestamp()) - 1631405340
            if timestamp < 0:
                print("error")
            if old_trip_id == row[0]:
                tstamp_array.append(timestamp)
                path_array.append([float(row[3]), float(row[2])])
            else:
                temp_dict = {}
                temp_dict['vendor'] = old_device_id
                temp_dict['path'] = path_array
                temp_dict['timestamps'] = tstamp_array
                json_array.append(temp_dict)
                old_device_id = int(row[1])
                old_trip_id = row[0]
                path_array = [[float(row[3]), float(row[2])]]
                tstamp_array = [timestamp]
        with open('data.json', 'w') as outfile:
            json.dump(json_array, outfile)

