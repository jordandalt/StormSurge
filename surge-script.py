import os, csv, re, calendar, operator
import dateutil.parser as parser
from datetime import date, timedelta
from ftplib import FTP

# open storm surge file, pulling list of surge dates
# this file should either be specified via command line prompts or fetched from a remote service
surgedatefile = input("Please specify relative path to surge date file (or just hit Return to use the default)... ")
try:
	surgehandle = open(surgedatefile, 'r')
except FileNotFoundError:
	surgehandle = open('2015_12_02_Dates.csv', 'r')
cleansurgehandle = open('output/surges_dates_clean.csv', 'w', newline='')
surgefile = csv.reader(surgehandle)
cleansurgefile = csv.writer(cleansurgehandle)
surgedates = {} #id:array(start,end) pairs

# open second surge file, pull stations of interest
# this file should either be specified via command line prompts or fetched from a remote service
stationsurgefile = input("Please specify relative path to surge station file (or just hit Return to use the default)... ")
try:
	stationhandle = open(stationsurgefile, 'r')
except FileNotFoundError:
	stationhandle = open('2015_12_02_All_Stations.csv', 'r')

stationfile = csv.reader(stationhandle)
surgestations = {} #id:array(station ids) pairs

outputhandle = open('output/extracted_data.csv', 'w', newline='')
outputfile = csv.writer(outputhandle)


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

next(stationfile) #skip first line
for row in stationfile:
	#if surge id exists in the dictionary, append the ID
	if row[0] in surgestations:
		surgestations[row[0]].append(row[3])
	else:
		surgestations[row[0]] = [row[3]]

ftp = FTP("ftp.ncdc.noaa.gov")
try:
	ftp.login()
	ftp.cwd('pub/data/ghcn/daily/all')
except Exception as e:
	print("Unable to access NOAA servers due to error:", e)

#iterate through surge events, open station files and then look for precip measurements from surge dates
totaldatecount = 0
missingdatecount = 0
nodatasurges = 0
for surge in surgestations:
	print("looking at surge id: ",surge)
	print("looking for dates: ",surgedates[surge][0].strftime("%Y %m %d"),"-",surgedates[surge][1].strftime("%Y %m %d"))

	surgeemptystations = 0
	surgetotalstations = len(surgestations[surge])
	#iterate through station ids
	for station in surgestations[surge]:
		missingfileflag = 0
		print("looking at station id: ",station)
		try:
			stationhandle = open('data/'+station+".dly","r")
			totaldatecount = totaldatecount + 1
		except FileNotFoundError:
			print("Station", station, "file missing! Attempting to download from NOAA...")
			try:
				newdly = open('data/'+station+".dly", 'wb')
				dlyname = station+".dly"
				ftp.retrbinary('RETR %s' % dlyname, newdly.write)
			except Exception as e:
				print("Unable to write new .dly file due to error:", e)

		#row heading we're searching for (this won't work if the surge event spans more than two months)
		rowheading_start = station+surgedates[surge][0].strftime("%Y%m")+"PRCP"
		rowheading_end = station+surgedates[surge][1].strftime("%Y%m")+"PRCP"

		#construct a date:precip dictionary with only valid dates for all months (up to two) covered by surge
		daypointer_start = parser.parse(surgedates[surge][0].strftime("%m 1 %Y"))
		daypointer_end = parser.parse(surgedates[surge][1].strftime("%m 1 %Y"))
		precipdays = {}

		if(stationhandle):
			missingfileflag = 1

		for line in stationhandle:
			if rowheading_start in line:
				daycounter = calendar.monthrange(daypointer_start.year, daypointer_start.month)[1]
				daypointer = daypointer_start
				line = line[21:].strip('\n')
				for i in range(0, len(line), 8):
					if daypointer >= surgedates[surge][0] and daypointer <= surgedates[surge][1] and daycounter > 0:
						#iterate through whole month, but only add dates to dictionary that are within range
						precipdays[daypointer] = line[i:i+5]
						print(surge, surgedates[surge][0].strftime("%Y%m%d")+"-"+surgedates[surge][1].strftime("%Y%m%d"), daypointer.strftime("%Y%m%d"), station, precipdays[daypointer])
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
						print(surge, surgedates[surge][0].strftime("%Y%m%d")+"-"+surgedates[surge][1].strftime("%Y%m%d"), daypointer.strftime("%Y%m%d"), station, precipdays[daypointer])
						outputfile.writerow([ surge, surgedates[surge][0].strftime("%Y%m%d")+"-"+surgedates[surge][1].strftime("%Y%m%d"), daypointer.strftime("%Y%m%d"), station, precipdays[daypointer]])
					daypointer = daypointer + timedelta(days=1)
					daycounter = daycounter - 1
		if len(precipdays) == 0 and missingfileflag: #write -9998 for dates missing from station file
			print("dates not found for surge", surge, "in station",station)
			daypointer = surgedates[surge][0]
			missingdatecount = missingdatecount + 1
			surgeemptystations = surgeemptystations + 1
			while daypointer <= surgedates[surge][1]:
				outputfile.writerow([surge, surgedates[surge][0].strftime("%Y%m%d")+"-"+surgedates[surge][1].strftime("%Y%m%d"), daypointer.strftime("%Y%m%d"), station, '-9998'])
				daypointer = daypointer + timedelta(days=1)

	# print("Surge ID",surge,"is missing data for",surgeemptystations,"out of",surgetotalstations,"stations!")
	if surgeemptystations == surgetotalstations:
		nodatasurges = nodatasurges + 1
print ("Number of missing dates:", missingdatecount, "out of", totaldatecount, "total surgedates")
print (nodatasurges,"surges have NO station data")
