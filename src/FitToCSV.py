import csv
import sys
from fitparse import FitFile

fitfile = FitFile(sys.argv[1])
output = sys.argv[1][0:len(sys.argv[1]) -3] + "csv"


with open(output, mode='w', newline= '') as file:
  writer = csv.writer(file)

  headers_written = False


  for record in fitfile.get_messages('record'):
    data = []
    data_names = []

    for record_data in record:
      data.append(record_data.value)
      data_names.append(record_data.name)

    if not headers_written:
      writer.writerow(data_names)
      headers_written = True

    writer.writerow(data)

