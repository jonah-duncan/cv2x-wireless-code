'''
Jonah Duncan, 04/11/24 - 05/30/24, CV2X Utility Tools
'''
import time
import os
import timeit
import matplotlib.pyplot as plt
import sys
import re
from operator import*

def CalibrateTime(runs: int) -> float:
    """
    Yields difference between GNSS time on MK6 and local time on PC.
    
    Args:
        runs (int): The number of calibrations to run.
    
    Returns:
        cal_avg (float): The average calibration time after runs
    """

    # Create empty array to hold calibration times (differences between MK6 and PC times)
    cal_time_arr = []

    # Variable to account for the delay in printing time on the MK6
    mk6_print_delay = 0.001

    # Compare PC-MK6 over specified runs unless runs is 0
    while((len(cal_time_arr) < runs) & (runs != 0)):

        # Save time prior to reading MK6 time
        pre_fetch_time = timeit.default_timer()

        # Open "dummy" file holding MK6-SSH (Putty) log times in binary mode
        with open('log.txt', 'rb') as log:
            
            # Find the last line in the file
            try:
                # Seek to the second-to-last character
                log.seek(-2, os.SEEK_END)

                # Read characters backwards until newline is found
                while log.read(1) != b'\n':

                    # Seek to the second-to-last character again (Note: Nested in another while loop)
                    log.seek(-2, os.SEEK_CUR)

            except OSError:
                # Seek the beginning of the log file
                log.seek(0)
            except KeyboardInterrupt:
                print('Interrupted:')
                break

            # Decode last line once it is found
            gnss_time = log.readline().decode()

            try:
                # Record GNSS time and account for the delay in printing time on the MK6
                gnss_time = float(gnss_time) - mk6_print_delay
            except:
                # Reset cal_time_arr for setting to error
                cal_time_arr = []

                # Ensure that gnss_time is a float for calculations below
                gnss_time = float("1000")

                # Tell user to run MK6 calibration command on MK6
                print('\nRun this MK6 Command to Calibrate Times:')
                print('while [ 1 ] ; do echo $EPOCHREALTIME ; sleep 0.001; done\n')

                # Set cal_time_arr to 0 to signify error
                cal_time_arr = [0]
                break
            
            # Save time after reading MK6 time
            post_fetch_time = timeit.default_timer()

            # Store current PC time and remove time taken to fetch GNSS
            pc_time = time.time() - (post_fetch_time - pre_fetch_time)

            # Calculate the difference between PC time and GNSS time
            cal_time = pc_time - gnss_time
            cal_time_arr.append(abs(cal_time))

    if(runs != 0):
        cal_avg = abs(sum(cal_time_arr) / len(cal_time_arr))
    else:
        cal_avg = 0
    return cal_avg

def CalibrationDialogue(cal_runs: int) -> float:
    """
    Prompts the user to calibrate times between GNSS (MK6) and PC.
    
    Args:
        cal_runs (int): The number of calibrations to run.
    
    Returns:
        cal_time (float): The average calibration time after runs.
    """

    cal_ans = input("\nPress Enter to calibrate MK6-PC times (or press Space + Enter again to skip)")
    if(cal_ans == ""):
        cal_time = CalibrateTime(cal_runs)
        if(cal_time != float(0)):
            print("\nAverage Calibration Time over " + str(cal_runs) + ' Samples: ' + str(cal_time) + "\n")
        else:
            input('Press Enter to calibrate MK6-PC times')
            cal_time = CalibrateTime(cal_runs)
            print("\nAverage Calibration Time over " + str(cal_runs) + ' Samples: ' + str(cal_time) + "\n")
    else:
        cal_time = float(0)
        print('\nContinuing without Calibration Time')

    return cal_time

def GetCoords() -> list:
    """
    Gets the coordinates of an MK6 from putty log files of connected PC. 
    
    Args:
        None
    
    Returns:
        coords (list): The coorinates of the connected MK6.
    """

    input("\nRun the following MK6 command to get its coordinates: \nkinematics-sample-client -a -n 1\n\nPress Enter after running MK6 command to store coordinates")

    # Create empty list for storing log lines
    coords = []

    # An average of 30 lines from the log of running MK6 command is enough
    gps_data_line_len = 30

    try:
        with open('log.txt') as file:
            
            # Loop to read iterate 
            # Last n lines and print it
            for line in (file.readlines() [-gps_data_line_len:]):
                coords.append(line)
        
        # Convert coords list into string
        coords = ' '.join([str(elem) for elem in coords])

        # Remove newlines characters -- make string one line
        coords = ''.join(coords.split('\n'))

        # Truncate string to only string between 'latitude' and 'altitude'
        coords = str(re.findall('latitude.+?altitude', coords))

        # Search for latitude and longitude numbers in coords string
        lat_match = re.search(r'latitude\s*-\s*([-0-9.]+)', coords)
        lon_match = re.search(r'longitude\s*-\s*([-0-9.]+)', coords)

        # Store latitude and longitude numbers
        latitude = float(lat_match.group(1))
        longitude = float(lon_match.group(1))

        # Pack latitude and longitude numbers into list for export
        coords = [latitude, longitude]
    except:
        coords = [0, 0]

    return coords