# Analyses

## Dry weather analysis

The inputs are:

* folder containing csv files of flow data from flowview containing the following columns:
  * _s\_depth_: depth measured in inches via sonar
  * _in_: depth measured in inches via pressure transducer
  * _ft/s_: velocity measured in inches via ADV
  * _MGD_: flow rate measured as producted of _in_ and _ft/s_
* a file containing daily rain totals in inches
* a file with details of each flow monitor including, where available:
  * associated rain gage
  * pipe diameter in inches
  * linear feet of pipe
  * basin area in acres
  * basin footprint in inch-miles
  * total footage in linear feet

Codes are written to find the following kids of information:

* the mean dry weather diurnal curve for (a)weekdays and (b)weekends
* the average dry weather flow rate for (a)weekdays and (b)weekends
* the groundwater infilration
* the sanitary flow diurnals for (a)weekdays and (b)weekends
* the sanitary flow averages for (a)weekdays and (b)weekends
* the base infiltration as a percent of the average flow
* the depth over the pipe diameter for (a)all days, (b)weekdays only, (c)weekends only

The output of the major analysis (flowMonitor.py) is dictionary containing:

* weekday values of d/D, gross Q, a dataframe with time of day as the index and individual dry dates as the columns
* weekend values of d/D, gross Q, a dataframe with time of day as the index and individual dry dates as the columns
* overall values of d/D and the base infiltration

## Wet weather analysis

The inputs are:

* folder containing csv files of flow data from flowview containing the following columns:
  * _s\_depth_: depth measured in inches via sonar
  * _in_: depth measured in inches via pressure transducer
  * _ft/s_: velocity measured in inches via ADV
  * _MGD_: flow rate measured as producted of _in_ and _ft/s_
* a file containing daily rain totals in inches
* a file containing hourly rain totals in inches
* a file with flowmonitors upstream of each particular flow monitor
* a file with details of each flow monitor including, where available:
  * associated rain gage
  * pipe diameter in inches
  * linear feet of pipe
  * basin area in acres
  * basin footprint in inch-miles
  * total footage in linear feet

text
