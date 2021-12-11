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

class Status:
    def __init__(self, vehicle_id, vehicle_type, vehicle_state, device_id, provider_id, provider_name, trip_id, event_time, event_type, battery_pct, event_gps_long, event_gps_lat, time):
        self.vehicle_id = vehicle_id
        self.vehicle_type = vehicle_type
        self.vehicle_state = vehicle_state
        self.device_id = device_id
        self.provider_id = provider_id
        self.provider_name = provider_name
        self.trip_id = trip_id
        self.event_time = event_time
        self.event_type = event_type
        self.battery_pct = battery_pct
        self.event_gps_long = event_gps_long
        self.event_gps_lat = event_gps_lat
        self.time = time
        if len(event_time) < 20:
            self.datetime = datetime.datetime.strptime(event_time, '%Y-%m-%d %H:%M:%S')
        else:
            self.datetime = datetime.datetime.strptime(event_time[:-7], '%Y-%m-%d %H:%M:%S')

#Encapsulates info about one specific trip for a scooter
class Vehicle:
    def __init__(self, vehicle_id, vehicle_type, provider_id, provider_name, trip_id, duration, distance, start, end, gps, tstamp):
        self.dev_id = vehicle_id
        self.type = vehicle_type
        self.provider_id = provider_id
        self.provider_name = provider_name
        self.trip_id = trip_id
        self.duration = int(duration)
        self.distance = int(distance)
        self.start = start #Cut off 3 zeros to get seconds
        self.end = end #Cut off 3 zeros to get seconds
        self.datetime = None #Will be overwritten later
        self.gps = gps
        self.gps_parsed = None #Array of GPS tuples
        self.tstamp = tstamp
        self.tstamp_parsed = None #Array of tstamp tuples

#Encapsulates all status info about a sepcific scooter (device id)
class Status_Collection:
    def __init__(self, vehicle_id, type, provider):
        self.vehicle_id = vehicle_id
        self.type = type
        self.provider = provider
        self.status_list = []

#Encapsulates all trip info about a specific scooter (device id)
class Vehicle_Collection:
    def __init__(self, dev_id, type, provider_name):
        self.dev_id = dev_id
        self.type = type
        self.provider_name = provider_name
        self.trip_list = []
        self.total_distance = 0 #Will be added onto later, in km (units)
        self.duration_seconds = None #Will be overwritten later
        self.duration_days = None #Will be overwritten later, = duration_seconds/(60*60*24)
        self.usage_times = None #Will be overwritten later
        self.working_time_seconds = None #Will be overwritten later
        self.working_time_days = None #Will be overwritten later, = working_time_seconds/(60*60*24)
        self.utilization = None #Will be overwritten later, utilization = time worked / total life time

#Helper method for parse_csv
def row_to_obj(row):
    if len(row) == 11:
        if int(row[7]) > 6000:
            if int(row[8])/1000 > 20:
                return Vehicle(row[1], row[2], row[4], row[5], row[6], "0", "0", row[9], row[10], None, None)
            return Vehicle(row[1], row[2], row[4], row[5], row[6], "0", row[8], row[9], row[10], None, None)
        if int(row[8])/1000 > 20:
            return Vehicle(row[1], row[2], row[4], row[5], row[6], row[7], "0", row[9], row[10], None, None)
        return Vehicle(row[1], row[2], row[4], row[5], row[6], row[7], row[8], row[9], row[10], None, None)
    else:
        if int(row[7]) > 6000:
            if int(row[8])/1000 > 20:
                return Vehicle(row[1], row[2], row[4], row[5], row[6], "0", "0", row[9], row[10], row[11], row[12])
            return Vehicle(row[1], row[2], row[4], row[5], row[6], "0", row[8], row[9], row[10], row[11], row[12])
        if int(row[8])/1000 > 20:
            return Vehicle(row[1], row[2], row[4], row[5], row[6], row[7], "0", row[9], row[10], row[11], row[12])
        return Vehicle(row[1], row[2], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12])

#Helper method for parse_status
def stat_row_to_obj(row):
    return Status(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],row[12])

#Helper method for parse_csv
def collection_list_update(collection_list, veh_object):
    for collection in collection_list:
        if collection.dev_id == veh_object.dev_id:
            collection.trip_list.append(veh_object)
            break
    else:
        collection_new = Vehicle_Collection(veh_object.dev_id, veh_object.type, veh_object.provider_name)
        collection_new.trip_list.append(veh_object)
        collection_list = np.append(collection_list, collection_new)
    return collection_list

#Helper method for parse_status
def stat_coll_update(stat_coll_list, stat):
    for coll in stat_coll_list:
        if coll.vehicle_id == stat.vehicle_id:
            coll.status_list.append(stat)
            break
    else:
        coll_new = Status_Collection(stat.vehicle_id, stat.vehicle_type, stat.provider_name)
        coll_new.status_list.append(stat)
        stat_coll_list = np.append(stat_coll_list, coll_new)
    return stat_coll_list

#Parse all csv trip files
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
            if len(row) == 0:
                continue
            if row[0] == '':
                continue
            veh = row_to_obj(row)
            collection_list = collection_list_update(collection_list, veh) 
    return collection_list

#Parses the all.csv file for status
def parse_status():
    stat_coll_list = np.array([])
    with open("status/all.csv", 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)
        for row in csvreader:
            if len(row) == 0:
                continue
            stat = stat_row_to_obj(row)
            stat_coll_list = stat_coll_update(stat_coll_list, stat)
    return stat_coll_list

#Sorts trip list in ascending order of "start" date
def sort_collection(collection_list):
    for collection in collection_list:
        trip_list = collection.trip_list
        for trip in trip_list:
            #date_string = trip.start
            trip.datetime = datetime.datetime.strptime(trip.start, '%Y-%m-%d %H:%M:%S')
            # trip.datetime = datetime.datetime.fromtimestamp(int(date_string))
            # trip.datetime = trip.datetime.replace(tzinfo=datetime.timezone.utc)
            # trip.datetime = trip.datetime.astimezone(ZoneInfo('US/Eastern'))
        trip_list.sort(key=lambda x: x.datetime)
        collection.trip_list = trip_list
    print("Sort collection is finished.")
    return collection_list

#Sorts trip list in ascending order of "start" date
def sort_status(collection_list):
    for collection in collection_list:
        trip_list = collection.status_list
        trip_list.sort(key=lambda x: x.datetime)
        collection.status_list = trip_list
    print("Sort status is finished.")
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

#Data is in meters, convert to km
def distance_traveled(collection_list):
    for collection in collection_list:
        trip_list = collection.trip_list
        for trip in trip_list:
            if (trip.distance/1000) > 20: #Threshold of 20km to remove outliers, can try higher thresholds
                collection.total_distance += 0
                continue
            collection.total_distance += (trip.distance/1000)
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
def plot_cdf(input_data, output_name, title_str, x_label, bin_count):
    if len(input_data) == 0:
        return
    count, bins_count = np.histogram(input_data, bins=bin_count)
    pdf = count / sum(count)
    cdf = np.cumsum(pdf)
    plt.plot(bins_count[1:], pdf, color="red", label="PDF")
    plt.plot(bins_count[1:], cdf, label="CDF")
    plt.legend()
    plt.title(title_str)
    plt.xlabel(x_label)
    plt.ylabel("Probability (%)")
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
    plot_cdf(usage_scooter, "usage_scooter", "CDF of # of Trips per Scooter", "# of Trips", 10)
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
    plot_cdf(distance_scooter, "distance_scooter", "CDF of Total Distance Traveled per Scooter", "Distance (km)", 10)
    #plot_cdf(distance_other, "distance_other")

#Plots the cdf of working time in terms of days
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
    plot_cdf(working_scooter, "working_scooter_days", "CDF of Total Active Travel Time per Scooter", "Time (Days)", 10)
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
    plot_cdf(duration_scooter, "duration_scooter_days", "CDF of Total Lifetime per Scooter", "Time (Days)", 10)
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
    plot_cdf(utilization_scooter, "utilization_scooter", "CDF of Utilization of Scooter (Travel Time / Lifetime)", "Percent (0.5 = 50%)", 10)
    #plot_cdf(utilization_other, "utilization_other")

def cdf_trip_distance(collection_list):
    trip_distance_scooter = []
    for collection in collection_list:
        for trip in collection.trip_list:
            if (trip.distance/1000) > 20: #Threshold of 20km to remove outliers, can try higher thresholds
                continue
            trip_distance_scooter.append(trip.distance/1000)
    plot_cdf(trip_distance_scooter, "trip_distance_scooter", "CDF of Individual Trip Distance", "Distance (km)", 10)

def cdf_trip_duration(collection_list):
    trip_duration_scooter = []
    for collection in collection_list:
        for trip in collection.trip_list:
            if trip.duration > 6000: #Threshold for outlier data
                continue
            trip_duration_scooter.append(trip.duration/60)
    plot_cdf(trip_duration_scooter, "trip_duration_scooter", "CDF of Individual Trip Duration", "Time (Minutes)", 10)

def cdf_main_drop(collection_list):
    main_drop = []
    for collection in collection_list:
        list_len = len(collection.status_list)
        status_list = collection.status_list
        for x in range(0, list_len):
            if status_list[x].event_type == "maintenance_pick_up":
                main_pick = status_list[x].datetime
                for y in range(x+1, list_len):
                    if status_list[y].event_type == "provider_drop_off":
                        drop_off = status_list[y].datetime
                        delta = (drop_off - main_pick).total_seconds()/3600 #Put in hours
                        if delta > 15:
                            main_drop.append(15)
                            break
                        main_drop.append(delta)
                        break
    plot_cdf(main_drop, "main_drop", "CDF of Time Interval between Maintenance and Dropoff", "Time (Hours)", 20)

def cdf_trip_intervals(collection_list):
    trip_intervals = []
    for collection in collection_list:
        list_len = len(collection.status_list)
        status_list = collection.status_list
        for x in range(0, list_len):
            if status_list[x].event_type == "trip_end":
                end = status_list[x].datetime
                for y in range(x+1, list_len):
                    if status_list[y].event_type == "trip_start":
                        start = status_list[y].datetime
                        delta = (start - end).total_seconds()/60 #Put in hours
                        if delta > 500:
                            trip_intervals.append(500)
                            break
                        trip_intervals.append(delta)
                        break
    plot_cdf(trip_intervals, "trip_intervals", "CDF of Time Interval between Consecutive Trips", "Time (Minutes)", 5)

#Plots all of the cdfs we want. Only use after organize_data()
def graph_functions(collection_list):
    # cdf_usage_times(collection_list)
    # cdf_distance_traveled(collection_list)
    # cdf_working_time(collection_list)
    # cdf_duration_days(collection_list)
    # cdf_utilization(collection_list)
    # cdf_trip_distance(collection_list)
    # cdf_trip_duration(collection_list)
    # plot_daily_trips(collection_list)
    box_trips(collection_list)
    box_duration(collection_list)
    box_length(collection_list)


def daily_trips(collection_list):
    trips_array = []
    for x in range(4, 10):
        for y in range(1, 31):
            day_trips = 0
            for collection in collection_list:
                for trip in collection.trip_list:
                    month = trip.datetime.month
                    day = trip.datetime.day
                    if x == month and y == day:
                        day_trips += 1
            trips_array.append(day_trips)
    return trips_array

def box_trips(collection_list):
    trips_hours = []
    for x in range(0, 24):
        temp_hours = []
        for y in range(1, 31):
            counter = 0
            for collection in collection_list:
                for trip in collection.trip_list:
                    hour = trip.datetime.hour
                    day = trip.datetime.day
                    if day != y:
                        continue
                    if x == hour:
                        counter += 1
            temp_hours.append(counter)
        trips_hours.append(np.asarray(temp_hours))
    plt.boxplot(trips_hours)
    plt.xlabel("Hours in the Day")
    plt.ylabel("# of Trips")
    plt.title("Average # of Trips Taken During \"x\" Hour in a Day")
    plt.savefig("boxplot_trips.png")
    plt.clf()

def box_duration(collection_list):
    trips_hours = []
    for x in range(0, 24):
        temp_hours = []
        for y in range(1, 31):
            for collection in collection_list:
                for trip in collection.trip_list:
                    hour = trip.datetime.hour
                    day = trip.datetime.day
                    if day != y:
                        continue
                    if x == hour:
                        temp_hours.append(trip.duration/60)
        count = 0
        for temp in temp_hours:
            if temp > 20:
                count += 1
        
        trips_hours.append(np.asarray(temp_hours))
    plt.boxplot(trips_hours)
    plt.xlabel("Hours in the Day")
    plt.ylabel("Time (Minutes)")
    plt.title("Average Duration of Trips Taken During \"x\" Hour in a Day")
    plt.savefig("boxplot_duration.png")
    plt.clf()

def box_length(collection_list):
    trips_hours = []
    for x in range(0, 24):
        temp_hours = []
        for y in range(1, 31):
            for collection in collection_list:
                for trip in collection.trip_list:
                    hour = trip.datetime.hour
                    day = trip.datetime.day
                    if day != y:
                        continue
                    if x == hour:
                        temp_hours.append(trip.distance/1000)
        trips_hours.append(np.asarray(temp_hours))
    plt.boxplot(trips_hours)
    plt.xlabel("Hours in the Day")
    plt.ylabel("Distance (km)")
    plt.title("Average Length of Trips Taken During \"x\" Hour in a Day")
    plt.savefig("boxplot_length.png")
    plt.clf()

def plot_daily_trips(collection_list):
    trips_array = daily_trips(collection_list)
    plot_cdf(trips_array, "trips_array", "CDF of # of Trips in One Day", "# of Trips", 10)
    temp = len(trips_array)//6 #6 Months of data
    xticks_list = [0, temp, temp*2, temp*3, temp*4, temp*5]
    xtick_labels = ["April", "May", "June", "July", "August", "September"]
    plt.plot(trips_array)
    plt.xticks(xticks_list, xtick_labels)
    plt.title("Number of Trips on Each Day")
    plt.xlabel("Date")
    plt.ylabel("# of Trips")
    plt.savefig("daily_trips.png")
    plt.clf()

#Find unique number of escooters in a particular month (dataset april - october) for the trips csv
def unique_scooters_trips_csv(collection_list):
    unique_scooters = [[], [], [], [], [], [], []]
    for x in range(4,11):
        for collection in collection_list:
            for trip in collection.trip_list:
                if trip.datetime.month != x:
                    continue
                if trip.dev_id not in unique_scooters[x-4]:
                    unique_scooters[x-4].append(trip.dev_id)
    return unique_scooters

#Find unique number of escooters in a particular month (dataset april - october) for the trips csv
def unique_scooters_status_csv(collection_list):
    unique_scooters = [[], [], [], [], [], [], []]
    for x in range(4,11):
        for collection in collection_list:
            for trip in collection.status_list:
                if trip.datetime.month != x:
                    continue
                if trip.vehicle_id not in unique_scooters[x-4]:
                    unique_scooters[x-4].append(trip.vehicle_id)
    return unique_scooters

def trip_status_breakdown(collection_list):
    unique_trips = [[0], [0], [0], [0], [0], [0], [0]]
    unique_status = [[0], [0], [0], [0], [0], [0], [0]]
    for x in range(4,11):
        for collection in collection_list:
            for trip in collection.status_list:
                if trip.datetime.month != x:
                    continue
                if trip.event_type == "trip_start" or trip.event_type == "trip_end":
                    (unique_trips[x-4])[0] = (unique_trips[x-4])[0] + 1
                else:
                    (unique_status[x-4])[0] = (unique_status[x-4])[0] + 1
    return [unique_trips, unique_status]

def maintenance_records(collection_list):
    count = 0
    for collection in collection_list:
        for trip in collection.status_list:
            if trip.event_type == "maintenance_pick_up":
                count += 1
                break
    return count

def status_statistics(stat_coll_list):
    unqiue_scooters = unique_scooters_status_csv(stat_coll_list)
    print("All unique scooters (trips and status)")
    print("April: " + str(len(unqiue_scooters[0])) + ", May: " + str(len(unqiue_scooters[1])) + ", June: " +
        str(len(unqiue_scooters[2])) + ", July: " + str(len(unqiue_scooters[3])) + ", August: " + str(len(unqiue_scooters[4])) +
        ", September: " + str(len(unqiue_scooters[5])) + ", October: " + str(len(unqiue_scooters[6])))

    temp = trip_status_breakdown(stat_coll_list)
    print("Number of trips per month")
    unqiue_scooters = temp[0]
    print("April: " + str(unqiue_scooters[0]) + ", May: " + str(unqiue_scooters[1]) + ", June: " +
        str(unqiue_scooters[2]) + ", July: " + str(unqiue_scooters[3]) + ", August: " + str(unqiue_scooters[4]) +
        ", September: " + str(unqiue_scooters[5]) + ", October: " + str(unqiue_scooters[6]))

    print("Number of status per month")
    unqiue_scooters = temp[1]
    print("April: " + str(unqiue_scooters[0]) + ", May: " + str(unqiue_scooters[1]) + ", June: " +
        str(unqiue_scooters[2]) + ", July: " + str(unqiue_scooters[3]) + ", August: " + str(unqiue_scooters[4]) +
        ", September: " + str(unqiue_scooters[5]) + ", October: " + str(unqiue_scooters[6]))

    print("Number of unique scooters that underwent maintenance: " + str(maintenance_records(stat_coll_list)))
    print("Number of total unique scooters: " + str(len(stat_coll_list)))

def statistics(collection_list):
    print("Number of vehicles: ", len(collection_list))

    types = []
    for collection in collection_list:
        if collection.type not in types:
            types.append(collection.type)
    print("Types of vehicles: ", *types)

    scoot_count = 0
    other_count = 0
    for collection in collection_list:
        if collection.type == "scooter":
            scoot_count += 1
        else:
            other_count += 1
    print("Number of Scooters: ", scoot_count)
    print("Number of Other: ", other_count)

    provs = []
    for collection in collection_list:
        if collection.provider_name not in provs:
            provs.append(collection.provider_name)
    print("Providers of escooters: ", *provs)

    total_dis = 0
    for collection in collection_list:
        total_dis += collection.total_distance
    print("Total Distance: ", total_dis)

    trip_ct = 0
    for collection in collection_list:
        trip_ct += len(collection.trip_list)
    print("Total Trip Count: ", trip_ct)

    unqiue_scooters = unique_scooters_trips_csv(collection_list)
    print("April: " + str(len(unqiue_scooters[0])) + ", May: " + str(len(unqiue_scooters[1])) + ", June: " +
        str(len(unqiue_scooters[2])) + ", July: " + str(len(unqiue_scooters[3])) + ", August: " + str(len(unqiue_scooters[4])) +
        ", September: " + str(len(unqiue_scooters[5])) + ", October: " + str(len(unqiue_scooters[6])))

def gps_parse(collection_list):
    temp_array = []
    for collection in collection_list:
        trip_list = collection.trip_list
        for trip in trip_list:
            if trip.gps == "[]":
                continue
            temp_array = []
            gps_strings = trip.gps.split("]")
            first_str = gps_strings[0]
            first_str = first_str[2:]
            first_str = first_str.split(",")
            first_str[1] = (first_str[1])[1:]
            temp_array.append((trip.trip_id, trip.dev_id, float(first_str[1]), float(first_str[0]))) #Lat and Long are flipped in data
            del gps_strings[0]
            del gps_strings[-1] #Two empty strings at end of split array
            del gps_strings[-1]
            for count, gps in enumerate(gps_strings):
                # if count % 2 == 1:
                #     continue
                tuple_temp = helper_gps_parse(gps)
                temp_array.append((trip.trip_id, trip.dev_id, tuple_temp[0], tuple_temp[1]))
            trip.gps_parsed = temp_array
    return collection_list

def helper_gps_parse(gps_str):
    gps_str = gps_str[3:]
    gps_str = gps_str.split(",")
    gps_str[1] = (gps_str[1])[1:]
    return (float(gps_str[1]), float(gps_str[0])) #Lat and Long are flipped in data

def gps_to_csv(collection_list):
    with open('gps.csv', 'w', newline='') as out:
        csv_out = csv.writer(out)
        csv_out.writerow(['trip id', 'device id', 'latitude', 'longitude', 'time'])
        for collection in collection_list:
            for trip in collection.trip_list:
                if trip.tstamp_parsed == None:
                    continue
                length = len(trip.tstamp_parsed)
                for x in range(length):
                    gps = trip.gps_parsed[x]
                    tstamp = trip.tstamp_parsed[x]
                    temp_date = datetime.datetime.fromtimestamp(tstamp/1000)
                    tstamp_str = temp_date.strftime("%Y-%m-%d %H:%M:%S")
                    result = (gps[0], gps[1], gps[2], gps[3], tstamp_str)
                    csv_out.writerow(result)

def gps_parse_first(collection_list):
    temp_array = []
    for collection in collection_list:
        trip_list = collection.trip_list
        for trip in trip_list:
            if trip.gps == "[]":
                continue
            gps_strings = trip.gps.split("]")
            first_str = gps_strings[0]
            first_str = first_str[2:]
            first_str = first_str.split(",")
            first_str[1] = (first_str[1])[1:]
            temp_array.append((float(first_str[1]), float(first_str[0]))) #Lat and Long are flipped in data
    return temp_array

def gps_parse_last(collection_list):
    temp_array = []
    for collection in collection_list:
        trip_list = collection.trip_list
        for trip in trip_list:
            if trip.gps == "[]":
                continue
            gps_strings = trip.gps.split("]")
            del gps_strings[-1] #Two empty strings at end of split array
            del gps_strings[-1]
            temp_array.append(helper_gps_parse(gps_strings[-1]))
    return temp_array

def tstamp_parse(collection_list):
    for collection in collection_list:
        for trip in collection.trip_list:
            temp_array = []
            if trip.tstamp == '[]':
                continue
            tstamp_strings = trip.tstamp.split("}")
            first_str = tstamp_strings[0]
            first_str = first_str.split(" ")
            temp_array.append(int(first_str[1]))
            del tstamp_strings[0]
            del tstamp_strings[-1] #Empty
            for tstamp in tstamp_strings:
                temp_array.append(tstamp_helper(tstamp))
            trip.tstamp_parsed = temp_array
    return collection_list

def tstamp_helper(tstamp_str):
    str_split = tstamp_str.split(" ")
    return int(str_split[2])



#Only function to be called in Main method. Performs all parsing, organizing, and analyzing.
def launch_script():
    collection_list = parse_all_files()
    collection_list = organize_data(collection_list)
    collection_list = gps_parse(collection_list)
    collection_list = tstamp_parse(collection_list)
    gps_to_csv(collection_list)
    #graph_functions(collection_list)
    #statistics(collection_list)
    #gps_array = gps_parse(collection_list)
    #gps_to_csv(gps_array)

    #stat_coll_list = parse_status()
    #stat_coll_list = sort_status(stat_coll_list)
    #status_statistics(stat_coll_list)
    #cdf_main_drop(stat_coll_list)
    #cdf_trip_intervals(stat_coll_list)

    print("Script is finished.")

#Main Method
if __name__ == "__main__":
    launch_script()
