import csv
import time
import datetime
import pandas as pd
import numpy as np
from dateutil.parser import parse
import matplotlib.pyplot as plt
import glob

#Encapsulates info about one specific trip for a scooter
class Vehicle:
    def __init__(self, id, dev_id, type, duration, distance, start, end, modified, month, hour, 
    day_week, council_start, council_end, year, census_start, census_end, start_central, end_central):
        self.id = id
        self.accuracy = accuracy
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

#Encapsulates all info about a specific scooter (device id)
class Vehicle_Collection:
    def __init__(self, dev_id, type):
        self.dev_id = dev_id
        self.type = type
        self.trip_list = []
        self.duration_seconds = None #Will be overwritten later
        self.duration_days = None #Will be overwritten later, = duration_seconds/(60*60*24)
        self.usage_times = None #Will be overwritten later
        self.working_time_seconds = None #Will be overwritten later
        self.working_time_slots = None #Will be overwritten later, one slot == 15 minutes
        self.utilization = None #Will be overwritten later, utilization = time worked / total life time

#Helper method for parse_csv
def row_to_obj(row):
    return Vehicle(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], 
    row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16], row[17])

#Helper method for parse_csv
def collection_list_update(collection_list, veh_object):
    for collection in collection_list:
        if collection.dev_id == veh_object.dev_id:
            collection.trip_list.append(veh_object)
            break
    else:
        collection_new = Vehicle_Collection(veh_object.dev_id, veh_object.type)
        collection_new.trip_list.append(veh_object)
        collection_list = np.append(collection_list, collection_new)
    return collection_list

def parse_all_files():
    collection_list = np.array([])
    for file in glob.glob("*.csv"):
        collection_list = parse_csv(file, collection_list)
        print("File Finished: ", file, ".")
    return collection_list

#Parses csv file to obtain a np array of "Vehicle_Collection" objects
def parse_csv(filename, collection_list):
    with open(filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)
        for row in csvreader:
            veh = row_to_obj(row)
            collection_list = collection_list_update(collection_list, veh) 
    return collection_list

#Sorts trip list in ascending order of "start" date
def sort_collection(collection_list):
    for collection in collection_list:
        trip_list = collection.trip_list
        for trip in trip_list:
            date_string = trip.start
            trip.datetime = parse(date_string, dayfirst=False)
        trip_list.sort(key=lambda x: x.datetime)
        collection.trip_list = trip_list
    print("Sort collection is finished.")
    return collection_list

#Total lifetime of scooter (includes idle and working days). Only use on sorted data
def duration_seconds(collection_list):
    for collection in collection_list:
        trip_list = collection.trip_list
        start_time = trip_list[0].datetime
        final_time = trip_list[-1].datetime
        duration = final_time - start_time
        duration_seconds = duration.total_seconds()
        collection.duration_seconds = duration_seconds
        collection.duration_days = duration_seconds / (60*60*24) #Seconds -> Minutes (60) -> Hours (60) -> Days (24)
    print("Duration seconds is finished.")
    return collection_list

#Add usage time (number of trips) to vehicle collection
def usage_times(collection_list):
    for collection in collection_list:
        trip_list = collection.trip_list
        collection.usage_times = len(trip_list)
    print("Usage time is finished.")
    return collection_list

#Add working_time (summation of all trip times) to vehicle collection
def working_time(collection_list):
    for collection in collection_list:
        trip_list = collection.trip_list
        working_time_seconds = 0
        for trip in trip_list:
            start_string = trip.start
            end_string = trip.end
            start_datetime = parse(start_string, dayfirst=False)
            end_datetime = parse(end_string, dayfirst=False)
            duration = end_datetime - start_datetime
            working_time_seconds = working_time_seconds + duration.total_seconds()
        collection.working_time_seconds = working_time_seconds
        collection.working_time_slots = working_time_seconds / (60*15) #Seconds -> Minutes (60) -> Slots (15)
    print("Working time is finished.")
    return collection_list

#Add utilization (working time / total life time) to vehicle collection. 
#Only use after duration_seconds() and working_time()
def utilization(collection_list):
    for collection in collection_list:
        working_time = collection.working_time_seconds
        lifetime = collection.duration_seconds
        if lifetime == 0: #Got a div by 0 error, possibly for a scooter that only had 1 trip (so start - final start = 0)
            collection.utilization = 0
        else:
            collection.utilization = working_time / lifetime
    print("Utilization is finished.")
    return collection_list

#Call on list of Vehicle_Collection before exporting to csv + plotting
def organize_data(collection_list):
    collection_list = sort_collection(collection_list)
    collection_list = duration_seconds(collection_list)
    collection_list = usage_times(collection_list)
    collection_list = working_time(collection_list)
    collection_list = utilization(collection_list)
    return collection_list

#Helper method for plotting cdf. input_data is a list of data (should be numeric). 
#output_name is a string to identify the figure. Do not include "_cdf.png" in the output_name string.
def plot_cdf(input_data, output_name):
    count, bins_count = np.histogram(input_data, bins=10)
    pdf = count / sum(count)
    cdf = np.cumsum(pdf)
    plt.plot(bins_count[1:], pdf, color="red", label="PDF")
    plt.plot(bins_count[1:], cdf, label="CDF")
    plt.legend()
    plt.savefig(output_name + "_cdf.png")
    plt.clf()

#Plots the cdf of usage times
def cdf_usage_times(collection_list):
    usage_both = []
    usage_scooter = []
    usage_other = []
    for collection in collection_list:
        usage_both.append(collection.usage_times)
        if collection.type == "scooter":
            usage_scooter.append(collection.usage_times)
        else:
            usage_other.append(collection.usage_times)
    plot_cdf(usage_both, "usage_both")
    plot_cdf(usage_scooter, "usage_scooter")
    plot_cdf(usage_other, "usage_other")

#Plots the cdf of working time in terms of slots (1 slot == 15 minutes)
def cdf_working_time(collection_list):
    working_both = []
    working_scooter = []
    working_other = []
    for collection in collection_list:
        working_both.append(collection.working_time_slots)
        if collection.type == "scooter":
            working_scooter.append(collection.working_time_slots)
        else:
            working_other.append(collection.working_time_slots)
    plot_cdf(working_both, "working_both_slots")
    plot_cdf(working_scooter, "working_scooter_slots")
    plot_cdf(working_other, "working_other_slots")

#Plots the cdf of lifetime of vehicle (both working and idle days) in days
def cdf_duration_days(collection_list):
    duration_both = []
    duration_scooter = []
    duration_other = []
    for collection in collection_list:
        duration_both.append(collection.duration_days)
        if collection.type == "scooter":
            duration_scooter.append(collection.duration_days)
        else:
            duration_other.append(collection.duration_days)
    plot_cdf(duration_both, "duration_both_days")
    plot_cdf(duration_scooter, "duration_scooter_days")
    plot_cdf(duration_other, "duration_other_days")

#Plots the cdf of utilization as a percent (0.5 -> 50% utilization)
def cdf_utilization(collection_list):
    utilization_both = []
    utilization_scooter = []
    utilization_other = []
    for collection in collection_list:
        utilization_both.append(collection.utilization)
        if collection.type == "scooter":
            utilization_scooter.append(collection.utilization)
        else:
            utilization_other.append(collection.utilization)
    plot_cdf(utilization_both, "utilization_both")
    plot_cdf(utilization_scooter, "utilization_scooter")
    plot_cdf(utilization_other, "utilization_other")

#Plots all of the cdfs we want. Only use after organize_data()
def graph_functions(collection_list):
    cdf_usage_times(collection_list)
    cdf_working_time(collection_list)
    cdf_duration_days(collection_list)
    cdf_utilization(collection_list)

#Only function to be called in Main method. Performs all parsing, organizing, and analyzing.
def launch_script():
    collection_list = parse_all_files()
    collection_list = organize_data(collection_list)
    graph_functions(collection_list)
    print("Script is finished.")

#Main Method
if __name__ == "__main__":
    launch_script()