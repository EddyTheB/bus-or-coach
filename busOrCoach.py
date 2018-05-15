# -*- coding: utf-8 -*-
"""
Created on Tue May  1 14:43:45 2018

@author: edward.barratt
"""

from collections import Counter
import os
import argparse
from selenium import webdriver
import pandas as pd
from fuzzywuzzy import process

try:
  import msvcrt # Good because users do not have to press enter
                # but unavaliable outside of windows.
  gotMSVCRT = True
except ImportError:
  gotMSVCRT = False


def getInput(text=None):
  if gotMSVCRT:
    if text is not None:
      print(text)
    r = msvcrt.getch().decode('ascii').upper()
    return r
  else:
    if text is None:
      text=''
    r = input(text)
    return r


def sortBusesFromCoaches(numberPlateList, baseurl='https://www.flickr.com/search/?text={}&sort=date-posted-desc',
                         data=None, vehRegPlateCol=None, metaCols={}):
  """
  Iterate through a list of registration numbers. For each number open a browser
  showing the Flikr search results for that registration number and ask the
  user to specify what sort of vehicle it is.

  Returns a dictionary where each registration number has a value in either
  B (for bus), C (for coach), M (for minibus), O (for other), or U for (unknown).
  """

  helpMessage = "Use 'X' to exit programme."
  if (data is not None) and (len(metaCols) > 0):
    gotMeta = True
    helpMessage += " Press 'U' (once) for meta data."
  else:
    gotMeta = False

  BCD = {'B': 'Bus', 'C': 'Coach', 'M': 'Minibus', 'O': 'Other', 'U': 'Unknown'}
  opts = list(BCD.keys())
  opts.append('X')
  busCoach = dict.fromkeys(numberPlateList, '-')
  driver = webdriver.Firefox()
  numberPlateC = Counter(numberPlateList)
  rnl = len(numberPlateC)
  for rni, (rn, N) in enumerate(numberPlateC.items()):
    if rni%10 == 0:
      print(helpMessage)
    url = baseurl.format(rn)
    BC = 'qqqq'
    while BC not in opts:
      print('{} of {} - {:>8} ({} occurrences): '.format(rni+1, rnl, rn, N), end='', flush=True)
      driver.get(url)
      print('Bus(B), Coach (C), Minibus(M), Other(O) or Unknown(U)? ', end='', flush=True)
      BC = getInput()
      BC = BC.upper()
      if BC not in opts:
        print('Input {} not understood.'.format(BC))
      if (BC == 'U') and (gotMeta):
        print('Unknown')
        print('Further Information:')
        for key, value in metaCols.items():
          print('  {}: {}'.format(key[3:-4], list(data.loc[data[vehRegPlateCol] == rn, value])[0]))
        print('Bus(B), Coach (C), Minibus(M), Other(O) or Unknown(U)? ', end='', flush=True)
        BC = getInput()
        BC = BC.upper()
    if BC in BCD.keys():
      print(BCD[BC])
      busCoach[rn] = BC
    else:
      print('Cancelled')
      break
  return busCoach

def testFromFile(inputfile=None, autoMiniBus=True,
                 startNew=False, busCoachColOut='BusCoach', vehRegPlateCol='Plate',
                 vehBodyCol='DVLA_VEHICLE_BODY', vehGrossWeightOCol='---',
                 vehMakeOCol='---', vehModelOCol='---',
                 vehUnladenWeightOCol='---', vehSeatingCapacityOCol='---',
                 busBodyTypes = ['S/D BUS/COACH', 'D/D BUS/COACH', 'H/D BUS/COACH', 'MINIBUS'],
                 trustPreviousDecisions=False, previousDecisionsFile=None,
                 **kwargs):
  """
  This is likely to only work on specific files.
  """

  if len(kwargs):
    print('The following keyword arguments were provided and are not recognised:')
    for kwarg in kwargs.keys():
      print(kwarg)
  LocalArgs = locals()

  if inputfile[-4:] == '.csv':
    data = pd.read_csv(inputfile)
  else:
    data = pd.read_excel(inputfile)

  allColumns = list(data)
  metaCols = {}
  for Arg, Value in LocalArgs.items():
    if Arg[-4:] == 'OCol':
      # Check that the optional column exists.
      if Value not in allColumns:
        bestOptions = process.extract(Value, allColumns, limit=5)
        posNames = "', '".join([x[0] for x in bestOptions])
        print(("\nOptional column {} does not exist in file, so will not be "
               "available for meta data options. You can specify another "
               "column using the --{} flag. Perhaps one of the "
               "following is appropriate: '{}'.").format(Value, Arg, posNames))
      else:
        metaCols[Arg] = Value
    elif Arg[-3:] == 'Col':
      # Check that the required column exists.
      if Value not in allColumns:
        bestOptions = process.extract(Value, allColumns, limit=5)
        posNames = '", "'.join([x[0] for x in bestOptions])
        raise ValueError(('Column {} does not exist in file, specify another '
                        'column using the --{} flag. Perhaps one of the '
                        'following is appropriate: "{}".').format(Value, Arg, posNames))

  print('{} records, {} unique registration plates.'.format(len(data.index), len(data[vehRegPlateCol].unique())))
  data_NB = data.loc[~data[vehBodyCol].isin(busBodyTypes)]
  if len(data_NB.index) > 0:
    print(("{} records removed due to unrecognised body types. Set "
           "'--busBodyTypes' if any need to be accepted.").format(len(data_NB.index)))
    print(data_NB[vehBodyCol].unique())
    print('Removed vehicle body types: {}.'.format(', '.join([str(x) for x in data_NB[vehBodyCol].unique()])))
    data = data.loc[data[vehBodyCol].isin(busBodyTypes)]
    print('{} records remaining, {} unique registration plates.'.format(len(data.index), len(data[vehRegPlateCol].unique())))

  data_orig = data.copy()

  BC_already = {}
  if trustPreviousDecisions:
    BC_already = getPreviousDecisions(previousDecisionsFile)
    regplates = BC_already.keys()
    regplatesnew = data[vehRegPlateCol].unique()
    BC_already = {r: BC_already[r] for r in regplates if r in regplatesnew}
    data_already = data.loc[data[vehRegPlateCol].isin(regplates)]
    data = data.loc[~data[vehRegPlateCol].isin(regplates)]
    print('{} already catagorised.'.format(len(data_already[vehRegPlateCol].unique())))

  if autoMiniBus:
    if vehGrossWeightOCol not in allColumns:
      print(("The normally optional column {} is required when --autoMiniBus "
             "is set to True.").format(vehGrossWeightOCol))

    data_minibus = data.loc[(data[vehBodyCol] == 'MINIBUS') &
                            (data[vehGrossWeightOCol] <= 3501)]
    data = data.loc[(data[vehBodyCol] != 'MINIBUS') |
                    (data[vehGrossWeightOCol] > 3501)]
    BC_minibus = dict.fromkeys(list(data_minibus[vehRegPlateCol]), 'M')
    print('{} automatically catagorised as minibuses.'.format(len(data_minibus.index)))
  else:
    BC_minibus = {}

  print('{} records remaining. {} unique registration numbers.'.format(len(data.index), len(set(data[vehRegPlateCol]))))
  if len(data.index) > 0:
    BC_rest = sortBusesFromCoaches(list(data[vehRegPlateCol]), data=data, vehRegPlateCol=vehRegPlateCol, metaCols=metaCols)
  else:
    BC_rest = {}

  print('Processing Complete.')
  yn = input('Update previously assigned values? [y/n]')
  if yn[0].upper() == 'Y':
    updatePreviousDecisions(previousDecisionsFile, {**BC_rest, **BC_already})

  BC = {**BC_already, **BC_minibus, **BC_rest}
  #for key, value in BC.items():
  #  print(key, value)
  data_orig[busCoachColOut] = data_orig.apply(lambda row: BC[row[vehRegPlateCol]], axis=1)

  savepath, savefile = os.path.split(inputfile)
  savefile, _ = os.path.splitext(savefile)
  if savefile[-3:] != '_BC':
    savefile = os.path.join(savepath, savefile+'_BC')
  else:
    savefile = os.path.join(savepath, savefile)
  tn = 0
  while os.path.exists(savefile+'.csv'):
    tn += 1
    savefile = savefile+'{}'.format(tn)
  savefile = savefile+'.csv'
  print('Results saved in {}.'.format(savefile))
  data_orig.to_csv(savefile)

def getPreviousDecisions(file, includeCity=False):
  prevDataDF = pd.read_csv(file)
  prevData = {}
  if includeCity:
    for ri, row in prevDataDF.iterrows():
      prevData[row['Plate'].replace(' ', '')] = {'BC': row['BusCoach'], 'City': row['City'].split(', ')}
  else:
    for ri, row in prevDataDF.iterrows():
      prevData[row['Plate'].replace(' ', '')] = row['BusCoach']
  return prevData

def updatePreviousDecisions(file, BC_new):

  cityName = input('What city name would you like to assign to the new records?')
  prevData = getPreviousDecisions(file, includeCity=True)
  gotReg = prevData.keys()
  for reg, value in BC_new.items():
    if value not in ['B', 'C']:
      continue
    if reg in gotReg:
      prevData[reg]['BC'] = value
      prevData[reg]['City'].append(cityName)
      prevData[reg]['City'] = list(set(prevData[reg]['City']))
    else:
      prevData[reg] = {'BC': value, 'City': [cityName]}
  prevDataDF = pd.DataFrame(columns=['Plate', 'BusCoach', 'City'])
  for reg, value in prevData.items():
    prevDataDF = prevDataDF.append(pd.DataFrame([[reg, value['BC'], ', '.join(value['City'])]], columns=['Plate', 'BusCoach', 'City']))
  prevDataDF.to_csv(file, index=False)
  print('Previous decision file updated.')

if __name__ == '__main__':

  desc = """
  A tool that helps the user to decide whether a particular registration
  number belongs to a bus or a coach.
  """
  parser = argparse.ArgumentParser(description=desc)
  parser.add_argument('inputfile', metavar='input file',
                      type=str,
                      help=("The file to process. This should be either an excel "
                            "file or a csv file. At a minimum the file should "
                            "contain a column or registration numbers. If the "
                            "string 'TEST' is supplied then a small set of test "
                            "registration numbers will be used to illustrate how "
                            "the tool works."))

  parser.add_argument('--vehRegPlateCol', metavar='vehicle registration plate column name',
                      type=str, nargs='?', default='PLATE',
                      help=("The column name for the vehicle registration "
                            "plate. Default 'PLATE'."))
  parser.add_argument('--busCoachColOut', metavar='bus or coach column name',
                      type=str, nargs='?', default='BusCoach',
                      help=("The name of the column that will be appended to "
                            "the input file, holding the values determining "
                            "bus form coach. Default 'BusCoach'."))
  parser.add_argument('--vehBodyCol', metavar='vehicle body type column name',
                      type=str, nargs='?', default='Body',
                      help=("The column name for the vehicle body type. "
                            "Default 'Body'."))
  parser.add_argument('--vehGrossWeightOCol', metavar='vehicle gross weight column name',
                      type=str, nargs='?', default='Gross Weight',
                      help=("The column name for the vehicle gross weight. Optional. "
                            "Default 'Gross Weight'."))
  parser.add_argument('--vehUnladenWeightOCol', metavar='vehicle unladen weight column name',
                      type=str, nargs='?', default='Unladen Weight',
                      help=("The column name for the vehicle unladen weight. Optional. "
                            "Default 'Unladen Weight'."))
  parser.add_argument('--vehMakeOCol', metavar='vehicle make column name',
                      type=str, nargs='?', default='Make',
                      help=("The column name for the vehicle make. Optional. "
                            "Default 'Make'."))
  parser.add_argument('--vehModelOCol', metavar='vehicle model column name',
                      type=str, nargs='?', default='Model',
                      help=("The column name for the vehicle make. Optional. "
                            "Default 'Model'."))
  parser.add_argument('--vehSeatingCapacityOCol', metavar='vehicle seating capacity name',
                      type=str, nargs='?', default='Seating Capacity',
                      help=("The column name for the vehicle seating capacity. Optional. "
                            "Default 'Seating Capacity'."))
  parser.add_argument('--autoMiniBus', metavar='detect minibuses automatically',
                      type=bool, nargs='?', default=True,
                      help=("If True, vehicles with a gross weight of 3500 kg "
                            "or less will be automatically assigned as "
                            "minibuses. If True, then an appropriate column "
                            "be specified for --vehGrossWeightOCol. Default True."))
  defaultbusBodyTypes = ['S/D BUS/COACH', 'D/D BUS/COACH', 'H/D BUS/COACH', 'MINIBUS']
  parser.add_argument('--busBodyTypes', metavar='bus or coach body classes',
                      type=str, nargs='*', default=defaultbusBodyTypes,
                      help=("Vehicle body classes that are considered to "
                            "represent vehicles that are either buses or coaches. "
                            "Default '{}'.").format("', '".join(defaultbusBodyTypes)))
  parser.add_argument('--trustPreviousDecisions', metavar='trust previous decisions',
                      type=bool, nargs='?', default=True,
                      help=("Will automatically assign the bus/coach value "
                            "that was previously assigned by a previous "
                            "operation. Default True."))
  parser.add_argument('--previousDecisionsFile', metavar='previous decisions file',
                      type=str, nargs='?', default='gotAlready.csv',
                      help=("File to use for the previous decisions. Default "
                            "True."))

  # More parameters to be added as needed.
  pargs = parser.parse_args()
  pargs = vars(pargs)

  if pargs['inputfile'] == 'TEST':
    rns = ['SK07CAA', 'SK07CAE', 'SK07CAO', 'SK07CAU', 'SK07CAV', 'SK07CAX',
          'SK07CBF', 'SK07CBU', 'SK07CBV', 'SK07CBX', 'SK07CBY', 'SK07CCA',
          'SK07CAA', 'SK07CAE', 'SK07CAO', 'SK07CAU', 'SK07CAA', 'SK07CAE']
    print('Running with test dataset.')
    BCs = sortBusesFromCoaches(rns)
    print('Test dataset sorted as follows:')
    for key, value in BCs.items():
      print('{}: {}'.format(key, value))
  else:
    testFromFile(**pargs)