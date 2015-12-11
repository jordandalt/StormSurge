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
	# how many months of data?
	targetmonths = (endyear - beginyear) * 12

	# take list of stations from surge-station CSV file
	stationsurgefile = input("Please specify relative path to surge station file (or just hit Return to use the default)... ")
	try:
		stationhandle = open(stationsurgefile, 'r')
	except FileNotFoundError:
		stationhandle = open('2015_12_02_All_Stations.csv', 'r')

	stationfile = csv.reader(stationhandle)
	stations = set()

	next(stationfile) #skip first line
	for row in stationfile:
		#building set of all station IDs
		if row[3] not in stations:
			stations.add(row[3])

	print ("Station ID\tMonths\ttMissing\tPercent Complete")
	monthcounts = []
	completepercents = []
	#open each station file and count the number of precip months
	for station in stations:
		monthcount = 0
		try:
			stationhandle = open('data/'+station+".dly","r")

		except FileNotFoundError:
			print("Station", station, "file missing!")

		for line in stationhandle:
			if station in line and "PRCP" in line:
				monthcount = monthcount + 1
		# if monthcount > targetmonths:
		monthcounts.append(monthcount)
		completepercents.append(monthcount/targetmonths*100)
		missingmonths = targetmonths - monthcount
		print (station,"\t",monthcount,"\t",missingmonths,"\t",monthcount/targetmonths*100,"%")

	# output months of data, total of missing months, percent of missing months for each station file
	print ("Out of",len(stations),"station files:")
	print ("Mean months of data:",numpy.mean(monthcounts))
	print ("Mean data completeness:",numpy.mean(completepercents),"%")
#defining "heavy" rainfall threshold.
# 90% threshold within each station
# OR 90% threshold within average of all stations associated with surge ID
#	(include n for each day of surge event)


if __name__ == "__main__":
	surgeQC()