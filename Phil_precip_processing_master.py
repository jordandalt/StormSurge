__author__ = 'toregozh'


surgefilename = "G:\\Philippine_Hazard\\Philippines_surges_try_python_csv_stripped.csv"
# surgefilename was created using surge data in ArcGIS. Some GIS Date functions were used to retrieve the values
# of month and year separately. The fields were then copied into CSV.

# all_file_lines = file.readlines()[1:] #returns a list of all rows and skips 1st row to remove headers
#
# print len(all_file_lines)
# print all_file_lines[1]

unique_month_year = []
uniq_yr = []
uniq_mon = []
surgefile_open = open(surgefilename, "r")
for line in surgefile_open:
    if(line[0]!="Y"): #skips 1st line
        if line not in unique_month_year:
            unique_month_year.append(line)
            fields = line.split(",")
            uniq_yr.append(fields[0])
            uniq_mon.append(fields[1])
print len(unique_month_year) #should be less than all_file_lines
print len(uniq_yr)
print len(uniq_mon) #should be == to uniq_yr & unique_month_year

surgefile_open.close()


# unique_split = [[int(elem) for elem in l.split(",")] for l in unique_month_year]
# print unique_split[0:5]

outDir = "G:\\Philippine_Hazard\\precip_python_processing\\"
outfilename = "Phil_precip_master.csv"
Phil_master_out = open(outDir + outfilename, "w")
Phil_master_out.write("LON,LAT,YEAR,MONTH,PRECIP\n")

for i in range(0, len(uniq_yr)):
    global_precip_file = open("precip." + uniq_yr[i])
    for line in global_precip_file:
        fields = line.split()
        longitude = float(fields[0])
        latitude = float(fields[1])
        precip = fields[(int(uniq_mon[i])+1)]
        if longitude > 118 and longitude < 126.75 and latitude > 7 and latitude < 18.75: #within PHIL boundaries
            str_line = ",".join([fields[0], fields[1], uniq_yr[i], uniq_mon[i], precip])
            Phil_master_out.write(str_line+"\n")

global_precip_file.close()
Phil_master_out.close()









