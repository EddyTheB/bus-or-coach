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


def sortBusesFromCoaches(numberPlateList, baseurl='https://www.flickr.com/search/?text=',
                         data=None, RegPlateCol=None):
  """
  Iterate through a list of registration numbers. For each number open a browser
  showing the Flikr search results for that registration number and ask the
  user to specify what sort of vehicle it is.

  Returns a dictionary where each registration number has a value in either
  B (for bus), C (for coach), M (for minibus), O (for other), or U for (unknown).
  """

  BCD = {'B': 'Bus', 'C': 'Coach', 'M': 'Minibus', 'O': 'Other', 'U': 'Unknown'}
  opts = list(BCD.keys())
  opts.append('X')
  busCoach = dict.fromkeys(numberPlateList, '-')
  driver = webdriver.Firefox()
  numberPlateC = Counter(numberPlateList)
  rnl = len(numberPlateC)
  for rni, (rn, N) in enumerate(numberPlateC.items()):
    if rni%10 == 0:
      print("Use 'X' to exit programme.")
    url = baseurl+rn
    BC = 'qqqq'
    while BC not in opts:
      print('{} of {} - {:>8} ({} occurrences): '.format(rni+1, rnl, rn, N), end='', flush=True)
      driver.get(url)
      print('Bus(B), Coach (C), Minibus(M), Other(O) or Unknown(U)? ', end='', flush=True)
      BC = getInput()
      BC = BC.upper()
      if BC not in opts:
        print('Input {} not understood.'.format(BC))
      if (BC == 'U') and (data is not None):
        print('Unknown')
        print('Further Information:')
        make = list(data.loc[data[RegPlateCol] == rn, 'MVRIS_MAKE_DESC'])[0]
        model = list(data.loc[data[RegPlateCol] == rn, 'MVRIS_MODEL_DESC'])[0]
        seats = list(data.loc[data[RegPlateCol] == rn, 'DVLA_VEHICLE_SEATING_CAPACITY'])[0]
        gw = list(data.loc[data[RegPlateCol] == rn, 'MVRIS_GROSS_WEIGHT'])[0]
        uw = list(data.loc[data[RegPlateCol] == rn, 'MVRIS_UNLADEN_WEIGHT'])[0]
        print('  Make:           {}'.format(make))
        print('  Model:          {}'.format(model))
        print('  Seats:          {}'.format(seats))
        print('  Gross Weight:   {}'.format(gw))
        print('  Unladen Weight: {}'.format(uw))
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

def testFromFile(filename, autoMiniBus=True,
                 startNew=False, BCCol='BusCoach', RegPlateCol='Plate',
                 busClasses = ['S/D BUS/COACH', 'D/D BUS/COACH', 'H/D BUS/COACH', 'MINIBUS']):
  """
  This is likely to only work on specific files.
  """

  if filename[-4:] == '.csv':
    data = pd.read_csv(filename)
  else:
    data = pd.read_excel(filename)

  print('{} records'.format(len(data.index)))
  data.loc[data['DVLA_VEHICLE_BODY'].isin(busClasses)]
  data_orig = data.copy()

  BC_already = {}
  if not startNew:
    if BCCol in list(data):
      redo = ['-', 'U', 'M']
      data_already = data.loc[~data[BCCol].isin(redo)]
      BC_already = pd.Series(data_already[BCCol].values, index=data_already[RegPlateCol]).to_dict()
      data = data.loc[data[BCCol].isin(redo)]
      print('{} already catagorised.'.format(len(data_already.index)))

  if autoMiniBus:
    data_minibus = data.loc[(data['DVLA_VEHICLE_BODY'] == 'MINIBUS') &
                            (data['MVRIS_GROSS_WEIGHT'] <= 3501)]
    data = data.loc[(data['DVLA_VEHICLE_BODY'] != 'MINIBUS') |
                    (data['MVRIS_GROSS_WEIGHT'] > 3501)]
    BC_minibus = dict.fromkeys(list(data_minibus[RegPlateCol]), 'M')
    print('{} automatically catagorised as minibuses.'.format(len(data_minibus.index)))
  else:
    BC_minibus = {}

  print('{} records remaining. {} unique registration numbers.'.format(len(data.index), len(set(data[RegPlateCol]))))
  BC_rest = sortBusesFromCoaches(list(data[RegPlateCol]), data=data, RegPlateCol=RegPlateCol)


  BC = {**BC_already, **BC_minibus, **BC_rest}
  #for key, value in BC.items():
  #  print(key, value)
  data_orig[BCCol] = data_orig.apply(lambda row: BC[row[RegPlateCol]], axis=1)

  savepath, savefile = os.path.split(filename)
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

  # More parameters to be added as needed.
  pargs = parser.parse_args()

  if pargs.inputfile == 'TEST':
    rns = ['SK07CAA', 'SK07CAE', 'SK07CAO', 'SK07CAU', 'SK07CAV', 'SK07CAX',
          'SK07CBF', 'SK07CBU', 'SK07CBV', 'SK07CBX', 'SK07CBY', 'SK07CCA',
          'SK07CAA', 'SK07CAE', 'SK07CAO', 'SK07CAU', 'SK07CAA', 'SK07CAE']
    print('Running with test dataset.')
    BCs = sortBusesFromCoaches(rns)
    print('Test dataset sorted as follows:')
    for key, value in BCs.items():
      print('{}: {}'.format(key, value))
  else:
    testFromFile(pargs.inputfile)