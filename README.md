# README #

A helper function to sort buses from coaches.

Created to assist with air quality modelling processes.

This programme iterates through a list of registration numbers. For each item it opens
a browser window and searches for images on Flickr related to that number. It turns out
that there is a large community of bus-spotters uploading photos tagged with registration
numbers onto Flickr. It is up to the user to decide whether the image is a bus or a coach.

If, for a particular registration number, the user selects "Unknown" (U) then some META data
about the vehicle will be presented, if available. If the user selects U again then the vehicle
will be recorded as "Unknown".

Clearly this is a somewhat labourious process, especially if the number of distinct
registration plates is large. There is scope to try machine learning tools to automatically
judge whether each image is of a bus or a coach, but I imagine that that is a difficult
judgement for a computer to make.

Some vehicles are clearly one or the other, but some judgement is required for other vehicles.
I have loosely been following the following guidelines, in this order:

 - If the gross weight is less than 3500kg, then it's a minibus.
 - If the vehicle is derived from an LGV, then it's a bus. For example a number of Ford Transit
   and Mercedes Sprinter type vehicles are altered to carry many more people than standard, and
   weigh more than 3500kg. For example the Mercedes vehicles that Rabbies tours use.
 - If the passenger compartment is low to the ground, such that wheelchair access would be
   straightforward, then it's a bus.
 - If the vehicle has luggage compartments beneath the passenger compartment, and passengers need
   to ascend steps to enter the cabin, then it's a coach.

## USAGE ##
```
$python .\busOrCoach.py -h
usage: busOrCoach.py [-h]
                     [--vehRegPlateCol [vehicle registration plate column name]]

                     [--busCoachColOut [bus or coach column name]]
                     [--vehBodyCol [vehicle body type column name]]
                     [--vehGrossWeightOCol [vehicle gross weight column name]]
                     [--vehUnladenWeightOCol [vehicle unladen weight column name
]]
                     [--vehMakeOCol [vehicle make column name]]
                     [--vehModelOCol [vehicle model column name]]
                     [--vehSeatingCapacityOCol [vehicle seating capacity name]]
                     [--autoMiniBus [detect minibuses automatically]]
                     [--busBodyTypes [bus or coach body classes [bus or coach bo
dy classes ...]]]
                     [--trustPreviousDecisions [trust previous decisions]]
                     [--previousDecisionsFile [previous decisions file]]
                     input file

A tool that helps the user to decide whether a particular registration number
belongs to a bus or a coach.

positional arguments:
  input file            The file to process. This should be either an excel
                        file or a csv file. At a minimum the file should
                        contain a column or registration numbers. If the
                        string 'TEST' is supplied then a small set of test
                        registration numbers will be used to illustrate how
                        the tool works.

optional arguments:
  -h, --help            show this help message and exit
  --vehRegPlateCol [vehicle registration plate column name]
                        The column name for the vehicle registration plate.
                        Default 'PLATE'.
  --busCoachColOut [bus or coach column name]
                        The name of the column that will be appended to the
                        input file, holding the values determining bus form
                        coach. Default 'BusCoach'.
  --vehBodyCol [vehicle body type column name]
                        The column name for the vehicle body type. Default
                        'Body'.
  --vehGrossWeightOCol [vehicle gross weight column name]
                        The column name for the vehicle gross weight.
                        Optional. Default 'Gross Weight'.
  --vehUnladenWeightOCol [vehicle unladen weight column name]
                        The column name for the vehicle unladen weight.
                        Optional. Default 'Unladen Weight'.
  --vehMakeOCol [vehicle make column name]
                        The column name for the vehicle make. Optional.
                        Default 'Make'.
  --vehModelOCol [vehicle model column name]
                        The column name for the vehicle make. Optional.
                        Default 'Model'.
  --vehSeatingCapacityOCol [vehicle seating capacity name]
                        The column name for the vehicle seating capacity.
                        Optional. Default 'Seating Capacity'.
  --autoMiniBus [detect minibuses automatically]
                        If True, vehicles with a gross weight of 3500 kg or
                        less will be automatically assigned as minibuses. If
                        True, then an appropriate column must be specified for
                        --vehGrossWeightOCol. Default True.
  --busBodyTypes [bus or coach body classes [bus or coach body classes ...]]
                        Vehicle body classes that are considered to represent
                        vehicles that are either buses or coaches. Default
                        'S/D BUS/COACH', 'D/D BUS/COACH', 'H/D BUS/COACH',
                        'MINIBUS'.
  --trustPreviousDecisions [trust previous decisions]
                        Will automatically assign the bus/coach value that was
                        previously assigned by a previous operation. Default
                        True.
  --previousDecisionsFile [previous decisions file]
                        File to use for the previous decisions. Default is the
                        'gotAlready.csv' file included.

```

## Requirments ##
Python3, including standard library.
pandas
selenium
fuzzywuzzy

Pandas is probably already installed, assuming you use a common Python package
such as Anaconda. Selenium and fuzzywuzzy may need installing seperately;
selenium is commonly used for testing web pages, fuzzywuzzy is used for fuzzy
string matching.

The code also assumes that firefox is installed.
