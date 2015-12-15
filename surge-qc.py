import os, csv, re, calendar, numpy

#QC check -- make sure stations are eligible for averaging by comparing each file's date range with desired date range.
# spoiler alert: most station files aren't going to be good.
def surgeQC (beginyear=-1, endyear=-1):

	# input beginning and end years for data
	if (beginyear == -1 or endeyar == -1):
		beginyear = input("Please specify beginning year for data set, or just hit enter for default (1950) ")
		if not beginyear:
			beginyear = 1950
		endyear = input("Please specify end year for data set, or just hit enter for default (2012)... ")
		if not endyear:
			endyear = 2012

	totaldays = 0
	for year in range(beginyear, endyear+1, 1):
		totaldays = totaldays + 366 if calendar.isleap(year) else totaldays + 365

	# take list of stations from surge-station CSV file
	stationsurgefile = input("Please specify relative path to surge station file (or just hit Return to use the default)... ")
	try:
		stationhandle = open(stationsurgefile, 'r')
	except FileNotFoundError:
		stationhandle = open('2015_12_02_All_Stations.csv', 'r')

	stationfile = csv.reader(stationhandle)
	stations = set()

	outputhandle = open('output/station_completeness_data.csv', 'w', newline='')
	outputfile = csv.writer(outputhandle)

	next(stationfile) #skip first line
	for row in stationfile:
		#building set of all station IDs
		if row[3] not in stations:
			stations.add(row[3])

	daycounts = []
	completepercents = []
	print ("Station ID\tTotal Days\tCompleteness")
	outputfile.writerow(["Station ID","Total Days","Completeness"])
	#open each station file and count the number of precip days within year range
	for station in stations:
		stationdaycount = 0
		try:
			stationhandle = open('data/'+station+".dly","r")

		except FileNotFoundError:
			print("Station", station, "file missing!")

		for line in stationhandle:
			if station in line and "PRCP" in line and int(line[11:15]) >= beginyear and int(line[11:15]) <= endyear:
				line = line[21:].strip('\n')
				for i in range(0, len(line), 8):
					if line[i:i+5] != '-9999':
						stationdaycount = stationdaycount + 1
		daycounts.append(stationdaycount)
		completepercents.append(stationdaycount/totaldays*100)
		outputfile.writerow([station,stationdaycount,str(stationdaycount/totaldays*100)+"%"])
		print (station,"\t",stationdaycount,"\t",stationdaycount/totaldays*100,"%")

	# output months of data, total of missing months, percent of missing months for each station file
	print ("Out of",len(stations),"station files:")
	print ("Mean days of data:",numpy.mean(daycounts))
	print ("Mean data completeness:",numpy.mean(completepercents),"%")

	#prompt for day count (percent?) threshold
	#return list of stations that are above threshold

#defining "heavy" rainfall threshold.
# 90% threshold within each station
# OR 90% threshold within average of all stations associated with surge ID
#	(include n for each day of surge event)


if __name__ == "__main__":
	surgeQC()