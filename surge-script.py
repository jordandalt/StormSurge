import os, csv, re, calendar, operator, numpy
import dateutil.parser as parser
from datetime import date, timedelta
from ftplib import FTP


# open second surge file, pull stations of interest
# this file should either be specified via command line prompts or fetched from a remote service

outputhandle = open('output/extracted_data.csv', 'w', newline='')
outputfile = csv.writer(outputhandle)

#takes the file name of a surge-date file, cleans and outputs to a new CSV file.
# returns a dictionary of start-end dates indexed on surge event IDs
def cleanDates (surgedatefilename, cleansurgefilename):
	try:
		surgehandle = open(surgedatefilename, 'r')
	except FileNotFoundError:
		print("Surge date file not found!")
	surgefile = csv.reader(surgehandle)
	try:
		cleansurgehandle = open(cleansurgefilename, 'w', newline='')
	except Exception as e:
		print("Unable to write new clean date file due to:", e)
	cleansurgefile = csv.writer(cleansurgehandle)
	surgedates = {} #id:array(start,end) pairs

	next(surgefile) #skip first line
	for row in surgefile:
		#parse out beginning and ending dates, add one day buffer on either side
		dates = row[4].split('-')
		startsurge = -1
		endsurge = -1

		#flexible date parsing -- THIS NEEDS TO BE TESTED WITH A LARGER DATA FILE
		#both dates have content
		if len(dates) == 2:
			# both dates contains alpha = surge spans multiple months
			month1 = re.search('[a-zA-Z]+', dates[0])
			month2 = re.search('[a-zA-Z]+', dates[1])
			if month1 and month2:
				startsurge = parser.parse(dates[0]+' '+row[3])
				endsurge = parser.parse(dates[1]+' '+row[3])
			# only one date contains alpha = range of days in month (9-12 sept) or stupid date format (9-aug)
			elif month1 or month2:
				#if only one date contains numbers, just combine them into a singe date
				if not(re.search('[0-9]+', dates[0])) or not(re.search('[0-9]+', dates[1])):
					# print("parsing ",dates[0]+' '+dates[1]+' '+row[3])
					startsurge = parser.parse(dates[0]+' '+dates[1]+' '+row[3])
					endsurge = startsurge
				#otherwise we have to get the month string and apply to both dates
				else:
					if month1:
						month = month1.group(0)
						# print("parsing ",dates[0]+row[3])
						startsurge = parser.parse(dates[0]+' '+row[3])
						# print("parsing ",dates[1]+' '+month+' '+row[3])
						endsurge = parser.parse(dates[1]+' '+month+' '+row[3])
					elif month2:
						month = month2.group(0)
						# print("parsing ",dates[0]+' '+month+' '+row[3])
						startsurge = parser.parse(dates[0]+' '+month+' '+row[3]) 
						# print("parsing ",dates[1]+row[3])
						endsurge = parser.parse(dates[1]+' '+row[3])
			# neither date contains alpha =  numeric date range (9/20-10/12)
			elif not(month1) and not(month2):
				startsurge = parser.parse(dates[0]+' '+row[3])
				endsurge = parser.parse(dates[1]+' '+row[3])
		#only one date has content
		elif len(dates) == 1:
			startsurge = parser.parse(dates[0]+' '+row[3])
			endsurge = startsurge

		# we want a one day buffer on either side
		startsurge = startsurge - timedelta(days=1)
		endsurge = endsurge + timedelta(days=1)

		# print ("Surge ID: ",row[0])
		# print ("Surge Date(s): ",startsurge,endsurge,"\n")
		surgedates[row[0]] = [startsurge,endsurge]

		#write to clean CSV file
		cleansurgefile.writerow([row[0],row[1],row[2],startsurge.strftime("%Y-%m-%d"),endsurge.strftime("%Y-%m-%d")])
	return surgedates

#takes a filename for a file containing surge IDs and weather station IDs
#   returns a dictionary of arrays of station IDs, indexed on surge event IDs
def getSurgeStations (surgestationfile):
	try:
		stationhandle = open(surgestationfile, 'r')

		stationfile = csv.reader(stationhandle)
		surgestations = {} #id:array(station ids) pairs

		next(stationfile) #skip first line
		for row in stationfile:
			#if surge id exists in the dictionary, append the ID
			if row[0] in surgestations:
				surgestations[row[0]].append(row[3])
			else:
				surgestations[row[0]] = [row[3]]
	except FileNotFoundError:
		print("Surge station file not found!")

	return surgestations

#takes a set of station IDs, looks for DLY files and downloads any missing files using FTP
def checkStationFiles(stationset):
	ftp = FTP("ftp.ncdc.noaa.gov")
	try:
		ftp.login()
		ftp.cwd('pub/data/ghcn/daily/all')
	except Exception as e:
		print("Unable to access NOAA servers due to error:", e)

	for station in stationset:
		try:
			stationhandle = open('data/'+station+".dly","r")
		except FileNotFoundError:
			print("Station", station, "file missing! Attempting to download from NOAA...")
			try:
				newdly = open('data/'+station+".dly", 'wb')
				dlyname = station+".dly"
				ftp.retrbinary('RETR %s' % dlyname, newdly.write)
			except Exception as e:
				print("Unable to write new .dly file due to error:", e)


#takes a set of stations and begin and end years, calculates completeness values
#   writes results to CSV file and returns dictionary of station:% completeness pairs
def getCompleteness (stationset, beginyear, endyear):
	totaldays = 0
	for year in range(beginyear, endyear+1, 1):
		totaldays = totaldays + 366 if calendar.isleap(year) else totaldays + 365

	outputhandle = open('output/station_completeness_data.csv', 'w', newline='')
	outputfile = csv.writer(outputhandle)

	completenessdata = {}

	outputfile.writerow(["Station ID","Total Days","Completeness"])
	#open each station file and count the number of precip days within year range
	for station in stationset:
		stationdaycount = 0
		try:
			stationhandle = open('data/'+station+".dly","r")

			for line in stationhandle:
				if station in line and "PRCP" in line and int(line[11:15]) >= beginyear and int(line[11:15]) <= endyear:
					line = line[21:].strip('\n')
					for i in range(0, len(line), 8):
						if line[i:i+5] != '-9999':
							stationdaycount = stationdaycount + 1

			stationdata = [station,stationdaycount,str(stationdaycount/totaldays*100)+"%"]
			outputfile.writerow(stationdata)
			completenessdata[station] = stationdaycount/totaldays*100
		except FileNotFoundError:
			print("Station", station, "file missing!")
	return completenessdata


#takes set of stations and calculates 90th percentile precip values
#   writes results to CSV file and returns directionary of station:precip pairs
def getStation90th(stationset):
	outputhandle = open('output/station_percentile_data.csv', 'w', newline='')
	outputfile = csv.writer(outputhandle)

	station90th = {}

	for station in stationset:
		precipvalues = []
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

		station90th[station] = numpy.percentile(precipvalues,90)
		outputfile.writerow([station, numpy.percentile(precipvalues,90)])

	return station90th

#takes dictionary of surge:station array pairs, calculates average daily precip for all stations
# def getSurge90th(surgestations, stationset):

#takes dictionary of surge:station array pairs and set of (thresholded) stations
#   writes results to CSV file
def getPrecipVals(surgestations, stationset):
	#iterate through surge events, open station files and then look for precip measurements from surge dates
	for surge in surgestations:
		print("looking at surge id: ",surge)
		#iterate through station ids
		for station in surgestations[surge]:
			if station in stationset: #threshold check!
				print("looking at station id: ",station)
				try:
					stationhandle = open('data/'+station+".dly","r")
				except FileNotFoundError:
					print("Station", station, "file missing!")

				#row heading we're searching for (this won't work if the surge event spans more than two months)
				rowheading_start = station+surgedates[surge][0].strftime("%Y%m")+"PRCP"
				rowheading_end = station+surgedates[surge][1].strftime("%Y%m")+"PRCP"

				#construct a date:precip dictionary with only valid dates for all months (up to two) covered by surge
				daypointer_start = parser.parse(surgedates[surge][0].strftime("%m 1 %Y"))
				daypointer_end = parser.parse(surgedates[surge][1].strftime("%m 1 %Y"))
				precipdays = {}

				for line in stationhandle:
					if rowheading_start in line:
						daycounter = calendar.monthrange(daypointer_start.year, daypointer_start.month)[1]
						daypointer = daypointer_start
						line = line[21:].strip('\n')
						for i in range(0, len(line), 8):
							if daypointer >= surgedates[surge][0] and daypointer <= surgedates[surge][1] and daycounter > 0:
								#iterate through whole month, but only add dates to dictionary that are within range
								precipdays[daypointer] = line[i:i+5]
								print(surge, daypointer.strftime("%Y%m%d"), station, precipdays[daypointer])
								outputfile.writerow([surge, surgedates[surge][0].strftime("%Y%m%d")+"-"+surgedates[surge][1].strftime("%Y%m%d"), daypointer.strftime("%Y%m%d"), station, precipdays[daypointer]])
							daypointer = daypointer + timedelta(days=1)
							daycounter = daycounter - 1
					elif rowheading_start != rowheading_end and rowheading_end in line:
						daycounter = calendar.monthrange(daypointer_end.year, daypointer_end.month)[1]
						daypointer = daypointer_end
						line = line[21:].strip('\n')
						for i in range(0, len(line), 8):
							if daypointer >= surgedates[surge][0] and daypointer <= surgedates[surge][1] and daycounter > 0:
								precipdays[daypointer] = line[i:i+5]
								print(surge, daypointer.strftime("%Y%m%d"), station, precipdays[daypointer])
								outputfile.writerow([ surge, surgedates[surge][0].strftime("%Y%m%d")+"-"+surgedates[surge][1].strftime("%Y%m%d"), daypointer.strftime("%Y%m%d"), station, precipdays[daypointer]])
							daypointer = daypointer + timedelta(days=1)
							daycounter = daycounter - 1
				if len(precipdays) == 0: #write -9998 for dates missing from station file
					print("dates not found for surge", surge, "in station",station)
					daypointer = surgedates[surge][0]
					while daypointer <= surgedates[surge][1]:
						outputfile.writerow([surge, surgedates[surge][0].strftime("%Y%m%d")+"-"+surgedates[surge][1].strftime("%Y%m%d"), daypointer.strftime("%Y%m%d"), station, '-9998'])
						daypointer = daypointer + timedelta(days=1)



if __name__ == "__main__":
	surgedatefile = input("Please specify relative path to surge date file (or just hit Return to use the default)... ")
	if not surgedatefile:
		surgedatefile = '2015_12_02_Dates.csv'
	cleansurgefilename = 'output/surges_dates_clean.csv'
	surgedates = cleanDates(surgedatefile, cleansurgefilename)
	# print(surgedates)

	stationsurgefile = input("Please specify relative path to surge station file (or just hit Return to use the default)... ")
	if not stationsurgefile:
		stationsurgefile = '2015_12_15_All_Stations_50km.csv'
	surgestations = getSurgeStations(stationsurgefile)
	# print(surgestations)

	#build set of all weather stations from surgestations dictionary
	stationset = set()
	for stationarray in surgestations.values():
		for station in stationarray:
			if station not in stationset:
				stationset.add(station)

	# print (stationset)

	print("Checking for missing DLY files...")
	checkStationFiles(stationset)

	beginyear = input("Please specify beginning year for data set, or just hit enter for default (1950) ")
	if not beginyear:
		beginyear = 1950
	endyear = input("Please specify end year for data set, or just hit enter for default (2012)... ")
	if not endyear:
		endyear = 2012

	print("Generating completeness data...")
	completenessdata = getCompleteness(stationset,beginyear,endyear)

	threshold = input("Please input completeness percentage threshold...")

	print("Thresholding stations...")
	threshstationset = set()
	for station,percentage in completenessdata.items():
		if percentage >= float(threshold):
			threshstationset.add(station)

	print("Calculating 90th percentile precipitation data for each station...")
	getStation90th(threshstationset)

	print("Generating daily precipitation values for surge events...")
	getPrecipVals(surgestations, threshstationset)





