import os, csv, re, calendar, operator
import dateutil.parser as parser
from datetime import date, timedelta

# open storm surge file, pulling list of surge dates
# this file should either be specified via command line prompts or fetched from a remote service
surgedatefile = input("Please specify relative path to surge date file (or just hit Return to use the default)... ")
try:
	surgehandle = open(surgedatefile, 'r')
except FileNotFoundError:
	surgehandle = open('data/2015_11_17_Surges_and_dates_JD.csv', 'r')
cleansurgehandle = open('data/surges_dates_clean.csv', 'w')
surgefile = csv.reader(surgehandle)
cleansurgefile = csv.writer(cleansurgehandle)
surgedates = {} #id:array(start,end) pairs

# open second surge file, pull stations of interest
# this file should either be specified via command line prompts or fetched from a remote service
stationsurgefile = input("Please specify relative path to surge station file (or just hit Return to use the default)... ")
try:
	stationhandle = open(stationsurgefile, 'r')
except FileNotFoundError:
	stationhandle = open('data/2015_11_17_Surges_and_precip_stations_JD.csv', 'r')

stationfile = csv.reader(stationhandle)
surgestations = {} #id:array(station ids) pairs

outputhandle = open('data/extracted_data.csv', 'w')
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

#iterate through surge events, open station files and then look for precip measurements from surge dates
for surge in surgestations:
	print("looking at surge id: ",surge)
	print("looking for dates: ",surgedates[surge][0].strftime("%Y %m %d"),"-",surgedates[surge][1].strftime("%Y %m %d"))
	#iterate through station ids
	for station in surgestations[surge]:
		print("looking at station id: ",station)
		stationhandle = open('data/'+station+".dly","r")

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
					while daycounter > 0:
						if daypointer >= surgedates[surge][0] and daypointer <= surgedates[surge][1]: 
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
					while daycounter > 0:
						if daypointer >= surgedates[surge][0] and daypointer <= surgedates[surge][1]:
							precipdays[daypointer] = line[i:i+5]
							print(surge, surgedates[surge][0].strftime("%Y%m%d")+"-"+surgedates[surge][1].strftime("%Y%m%d"), daypointer.strftime("%Y%m%d"), station, precipdays[daypointer])
							outputfile.writerow([ surge, surgedates[surge][0].strftime("%Y%m%d")+"-"+surgedates[surge][1].strftime("%Y%m%d"), daypointer.strftime("%Y%m%d"), station, precipdays[daypointer]])
						daypointer = daypointer + timedelta(days=1)
						daycounter = daycounter - 1
