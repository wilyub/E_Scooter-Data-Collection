import csv
import time
import datetime
import pandas as pd
import numpy as np
from dateutil.parser import parse
import matplotlib.pyplot as plt

class Vehicle:
    def __init__(self, id, dev_id, type, duration, distance, start, end, modified, month, hour, 
    day_week, council_start, council_end, year, census_start, census_end, start_central, end_central):
        self.id = id
        self.dev_id = dev_id
        self.type = type
        self.duration = duration
        self.distance = distance
        self.start = start
        self.end = end
        self.modified = modified
        self.month = month
        self.hour = hour
        self.day_week = day_week
        self.council_start = council_start
        self.council_end = council_end
        self.year = year 
        self.census_start = census_start
        self.census_end = census_end
        self.start_central = start_central
        self.end_central = end_central
        self.datetime = None #Will be overwritten later

class Vehicle_Collection:
    def __init__(self, dev_id, type):
        self.dev_id = dev_id
        self.type = type
        self.trip_list = []
        self.duration_seconds = None #Will be overwritten later
        self.usage_times = None #Will be overwritten later

def row_to_obj(row):
    return Vehicle(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], 
    row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16], row[17])

def collection_list_update(collection_list, veh_object):
    for collection in collection_list:
        if collection.dev_id == veh_object.dev_id:
            collection.trip_list.append(veh_object)
            break
    else:
        collection_new = Vehicle_Collection(veh_object.dev_id, veh_object.type)
        collection_new.trip_list.append(veh_object)
        collection_list = np.append(collection_list, collection_new)
        #collection_list.append(collection_new)
    return collection_list

def parse_csv():
    filename = "scooter_data.csv"
    fields = []
    collection_list = np.array([])
    with open(filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        fields = next(csvreader)
        start = time.time()
        for row in csvreader:
            veh = row_to_obj(row)
            collection_list = collection_list_update(collection_list, veh) 
            if (csvreader.line_num % 1000) == 0:
                end = time.time()
                print("No. : %d"%(csvreader.line_num))
                print("Time for add: ", (end-start), "sec")
                print("Length of np array: ", collection_list.size)
                start = time.time()  
    return collection_list

def sort_collection(collection_list):
    for collection in collection_list:
        trip_list = collection.trip_list
        for trip in trip_list:
            date_string = trip.start
            trip.datetime = parse(date_string, dayfirst=False)
        trip_list.sort(key=lambda x: x.datetime)
        collection.trip_list = trip_list
    return collection_list

#Only use on sorted lists
def duration_seconds(collection_list):
    for collection in collection_list:
        trip_list = collection.trip_list
        start_time = trip_list[0].datetime
        final_time = trip_list[-1].datetime
        duration = final_time - start_time
        duration_seconds = duration.total_seconds()
        collection.duration_seconds = duration_seconds
    return collection_list

def usage_times(collection_list):
    for collection in collection_list:
        trip_list = collection.trip_list
        collection.usage_times = len(trip_list)
    return collection_list

#Call on list of Vehicle_Collection before exporting to csv + plotting
def organize_data(collection_list):
    collection_list = sort_collection(collection_list)
    collection_list = duration_seconds(collection_list)
    collection_list = usage_times(collection_list)

    return collection_list

def cdf_usage_times(collection_list):
    usage_list = []
    for collection in collection_list:
        usage_list.append(collection.usage_times)
    count, bins_count = np.histogram(usage_list, bins=10)
    pdf = count / sum(count)
    cdf = np.cumsum(pdf)
    plt.plot(bins_count[1:], pdf, color="red", label="PDF")
    plt.plot(bins_count[1:], cdf, label="CDF")
    plt.legend()
    plt.savefig('usage_times_cdf.png')

if __name__ == "__main__":
    #test_list = parse_csv()
    Vehicle1 = Vehicle(1, 1, 1, 1, 1, '05/29/2020 02:15:00 AM', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
    Vehicle2 = Vehicle(1, 1, 1, 1, 1, '04/18/2020 05:15:00 AM', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
    Vehicle3 = Vehicle(1, 1, 1, 1, 1, '04/18/2020 05:00:00 AM', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
    Vehicle4 = Vehicle(1, 1, 1, 1, 1, '03/29/2020 02:15:00 AM', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
    Vehicle5 = Vehicle(1, 1, 1, 1, 1, '05/18/2020 05:15:00 AM', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
    Vehicle6 = Vehicle(1, 1, 1, 1, 1, '04/18/2020 05:00:00 AM', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
    col_test = Vehicle_Collection(1, 1)
    col_test.trip_list = [Vehicle1, Vehicle2, Vehicle3]
    col_test_2 = Vehicle_Collection(1,1)
    col_test_2.trip_list = [Vehicle4, Vehicle5, Vehicle6]
    test_list = [col_test, col_test_2]

    col1 = Vehicle_Collection(1,1)
    col2 = Vehicle_Collection(1,1)
    col3 = Vehicle_Collection(1,1)
    col4 = Vehicle_Collection(1,1)
    col5 = Vehicle_Collection(1,1)
    col6 = Vehicle_Collection(1,1)
    col7 = Vehicle_Collection(1,1)
    col8 = Vehicle_Collection(1,1)
    col9 = Vehicle_Collection(1,1)    
    col10 = Vehicle_Collection(1,1)
    col11 = Vehicle_Collection(1,1)
    col12 = Vehicle_Collection(1,1)
    col13 = Vehicle_Collection(1,1)
    col14 = Vehicle_Collection(1,1)
    col16 = Vehicle_Collection(1,1)
    col15 = Vehicle_Collection(1,1)
    col17 = Vehicle_Collection(1,1)
    col18 = Vehicle_Collection(1,1)
    col19 = Vehicle_Collection(1,1)
    col20 = Vehicle_Collection(1,1)
    col21 = Vehicle_Collection(1,1)
    col22 = Vehicle_Collection(1,1)
    col23 = Vehicle_Collection(1,1)

    col1.usage_times = 42
    col2.usage_times = 43
    col3.usage_times = 45
    col4.usage_times = 20
    col5.usage_times = 25
    col6.usage_times = 36
    col7.usage_times = 50
    col8.usage_times = 42
    col9.usage_times = 33
    col10.usage_times = 44
    col11.usage_times = 28
    col12.usage_times = 40
    col13.usage_times = 4
    col14.usage_times = 39
    col15.usage_times = 43
    col16.usage_times = 25
    col17.usage_times = 34
    col18.usage_times = 37
    col19.usage_times = 21
    col20.usage_times = 16
    col21.usage_times = 18
    col22.usage_times = 23
    col23.usage_times = 20

    test_col = [col1, col2, col3, col4, col5, col6, col7, col8, col9, col10,
    col11, col12, col13, col14, col15, col16, col17, col18, col19, col20, col21, col22, col23]
    cdf_usage_times(test_col)


    #new_list = organize_data(test_list)

    print("yay")