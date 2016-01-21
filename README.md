# StormSurge
Parses a collection of data files to calculate the relationship between known historic storm surges and precipitation measurements at nearby weather stations.

Required inputs:
- CSV file with surge IDs, locations (lat/long), and dates
- CSV file with surge IDs, locations (optional), and weather station IDs

Optional input:
- .dly files of related weather stations in 'data' directory

Outputs:
- CSV file of cleaned surge date ranges
- CSV file of "completeness" values for all supplied weather stations
- CSV file of 90th percentile precipitation values for all weather stations above a user-defined completeness threshold
- CSV file of daily precipitation measurements for each day of surge event (-/+ 1 day) for each weather station (that meets completeness threshold)

