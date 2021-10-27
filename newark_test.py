import csv
from os import startfile
import time
import datetime
import pandas as pd
import numpy as np
from dateutil.parser import parse
import matplotlib.pyplot as plt
import glob

#Encapsulates info about one specific trip for a scooter
class Vehicle:
    def __init__(self, vehicle_id, vehicle_type, provider_id, provider_name, trip_id, duration, distance, start, end):
        self.dev_id = vehicle_id
        self.type = vehicle_type
        self.provider_id = provider_id
        self.provider_name = provider_name
        self.trip_id = trip_id
        self.duration = int(duration)
        self.distance = int(distance)
        self.start = start[:-3] #Cut off 3 zeros to get seconds
        self.end = end[:-3] #Cut off 3 zeros to get seconds
        self.datetime = None #Will be overwritten later

#Encapsulates all info about a specific scooter (device id)
class Vehicle_Collection:
    def __init__(self, dev_id, type):
        self.dev_id = dev_id
        self.type = type
        self.trip_list = []
        self.total_distance = 0 #Will be added onto later
        self.duration_seconds = None #Will be overwritten later
        self.duration_days = None #Will be overwritten later, = duration_seconds/(60*60*24)
        self.usage_times = None #Will be overwritten later
        self.working_time_seconds = None #Will be overwritten later
        self.working_time_days = None #Will be overwritten later, = working_time_seconds/(60*60*24)
        self.utilization = None #Will be overwritten later, utilization = time worked / total life time

#Helper method for parse_csv
def row_to_obj(row):
    return Vehicle(row[1], row[2], row[4], row[5], row[6], row[7], row[8], row[9], row[10])

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
    for file in glob.glob("data/*.csv"):
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
            trip.datetime = datetime.datetime.fromtimestamp(int(date_string))
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

def distance_traveled(collection_list):
    for collection in collection_list:
        trip_list = collection.trip_list
        for trip in trip_list:
            collection.total_distance += trip.distance
    print("Distance traveled is finished.")
    return collection_list

#Add working_time (summation of all trip times) to vehicle collection
def working_time(collection_list):
    for collection in collection_list:
        trip_list = collection.trip_list
        working_time_seconds = 0
        for trip in trip_list:
            working_time_seconds += trip.duration
        collection.working_time_seconds = working_time_seconds
        collection.working_time_days = working_time_seconds/(60*60*24)
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
    collection_list = distance_traveled(collection_list)
    collection_list = working_time(collection_list)
    collection_list = utilization(collection_list)
    return collection_list

#Helper method for plotting cdf. input_data is a list of data (should be numeric). 
#output_name is a string to identify the figure. Do not include "_cdf.png" in the output_name string.
def plot_cdf(input_data, output_name):
    if len(input_data) == 0:
        return
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
    #Only scooter data atm
    #plot_cdf(usage_both, "usage_both")
    plot_cdf(usage_scooter, "usage_scooter")
    #plot_cdf(usage_other, "usage_other")


def cdf_distance_traveled(collection_list):
    distance_both = []
    distance_scooter = []
    distance_other = []
    for collection in collection_list:
        distance_both.append(collection.total_distance)
        if collection.type == "scooter":
            distance_scooter.append(collection.total_distance)
        else:
            distance_other.append(collection.total_distance)
    #plot_cdf(distance_both, "distance_both")
    plot_cdf(distance_scooter, "distance_scooter")
    #plot_cdf(distance_other, "distance_other")

#Plots the cdf of working time in terms of slots (1 slot == 15 minutes)
def cdf_working_time(collection_list):
    working_both = []
    working_scooter = []
    working_other = []
    for collection in collection_list:
        working_both.append(collection.working_time_days)
        if collection.type == "scooter":
            working_scooter.append(collection.working_time_days)
        else:
            working_other.append(collection.working_time_days)
    #plot_cdf(working_both, "working_both_slots")
    plot_cdf(working_scooter, "working_scooter_days")
    #plot_cdf(working_other, "working_other_slots")

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
    #plot_cdf(duration_both, "duration_both_days")
    plot_cdf(duration_scooter, "duration_scooter_days")
    #plot_cdf(duration_other, "duration_other_days")

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
    #plot_cdf(utilization_both, "utilization_both")
    plot_cdf(utilization_scooter, "utilization_scooter")
    #plot_cdf(utilization_other, "utilization_other")

#Plots all of the cdfs we want. Only use after organize_data()
def graph_functions(collection_list):
    cdf_usage_times(collection_list)
    cdf_distance_traveled(collection_list)
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