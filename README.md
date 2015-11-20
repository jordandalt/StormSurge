# StormSurge
Parses a collection of data files to calculate the relationship between known historic storm surges and precipitation measurements at nearby weather stations.

Required inputs:
- CSV file with surge IDs, locations (lat/long), and dates
- CSV file with surge IDs, locations (optional), and weather station IDs
- .dly files of related weather stations

Outputs:
- CSV file of cleaned surge date ranges
- CSV file of daily precipitation measurements for each day of surge event (-/+ 1 day) for each weather station near surge event

To-do:
- Additional data analysis on precipitation measurements
- Automate file retrieval process (FTP retrieval of .dly files from NOAA?)

