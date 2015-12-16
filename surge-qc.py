import os, csv, re, calendar, numpy

#QC check -- make sure stations are eligible for averaging by comparing each file's date range with desired date range.
# iterates through all stations, prints total days within specified range and 90th precip percentile for each station
# if threshold provided, only outputs percentiles for stations above threshold
def surgeQC (beginyear, endyear, threshold):

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

	print ("Station ID\tTotal Days\tCompleteness\t90th Percentile Precip")
	outputfile.writerow(["Station ID","Total Days","Completeness","90th Percentile Precip"])
	#open each station file and count the number of precip days within year range
	for station in stations:
		stationdaycount = 0
		precipvalues = []
		precipval = ''
		try:
			stationhandle = open('data/'+station+".dly","r")

		except FileNotFoundError:
			print("Station", station, "file missing!")

		for line in stationhandle:
			if station in line and "PRCP" in line and int(line[11:15]) >= beginyear and int(line[11:15]) <= endyear:
				line = line[21:].strip('\n')
				for i in range(0, len(line), 8):
					if line[i:i+5] != '-9999':
						precipvalues.append(float(line[i:i+5]))
						stationdaycount = stationdaycount + 1
		daycounts.append(stationdaycount)
		completepercents.append(stationdaycount/totaldays*100)

		if threshold and (stationdaycount/totaldays*100) >= float(threshold):
			precipval = numpy.percentile(precipvalues,90)
		elif not threshold and precipvalues:
			precipval = numpy.percentile(precipvalues,90)
		stationdata = [station,stationdaycount,str(stationdaycount/totaldays*100)+"%",str(precipval)]
		outputfile.writerow(stationdata)
		print (station,stationdaycount,str(stationdaycount/totaldays*100)+"%",str(precipval))

	# output months of data, total of missing months, percent of missing months for each station file
	print ("Out of",len(stations),"station files:")
	print ("Mean days of data:",numpy.mean(daycounts))
	print ("Mean data completeness:",numpy.mean(completepercents),"%")

# TO DO: 90% threshold within average of all stations associated with surge ID
#	(include n for each day of surge event)


if __name__ == "__main__":
	beginyear = input("Please specify beginning year for data set, or just hit enter for default (1950) ")
	if not beginyear:
		beginyear = 1950
	endyear = input("Please specify end year for data set, or just hit enter for default (2012)... ")
	if not endyear:
		endyear = 2012
	#prompt for day count (percent?) threshold
	threshold = input("Please specify completeness threshold (just hit enter to return all stations)...")
	if not threshold:
		threshold = None
	surgeQC(beginyear,endyear,threshold)
