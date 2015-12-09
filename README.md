# StormSurge
Parses a collection of data files to calculate the relationship between known historic storm surges and precipitation measurements at nearby weather stations. NOTE: if the script does not find any of the .dly files specified by the input files, it will automatically download the updated files from NOAA's FTP repository. Please re-run the script if this is the case.

Required inputs:
- CSV file with surge IDs, locations (lat/long), and dates
- CSV file with surge IDs, locations (optional), and weather station IDs

Optional input:
- .dly files of related weather stations in 'data' directory

Outputs:
- CSV file of cleaned surge date ranges
- CSV file of daily precipitation measurements for each day of surge event (-/+ 1 day) for each weather station near surge event

To-do:
- Additional data analysis on precipitation measurements

