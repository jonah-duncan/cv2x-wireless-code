'''
Jonah Duncan, 04/11/24 - 05/30/24, CV2X Receiver Tools
'''
import time
import socket
import sys
import pickle
import datetime
from operator import*

# Ignore warnings here -- importing self-made packages
import utilities as ut

import geopy.distance

def ReceivePackets(mk6_addr: str, mk6_port: int, pkt_tot: int, cal_runs: int) -> None:
    """
    Receive [pkt_tot] UDP packets from IPv4 IP [mk6_addr] on port [mk6_port] with [cal_runs] calibration runs.

    Args:
        mk6_addr (str): The IP address of the MK6 radio.
        mk6_port (int): The port of the MK6 radio.
        pkt_tot  (int): The number of packets to receive.
        cal_runs (int): The number of calibration runs to undergo
    
    Returns:
        None

    ==============================================================

    TX                     RX
    +---+                  +-------------------------------------+
    |   | [acme at 5.9GHz] | +-----+ (mk6_addr, mk6_port) +----+ |
    |   |----------------->| | MK6 |--------------------->| PC | |
    |   | pkt_tot pkts     | +-----+ pkt_tot udp pkts     +----+ |
    |   | as bytes         |  bytes                        dict  |
    +---+                  +-------------------------------------+

    1. Retrieve receiver coordinates from [log.txt] and calculate distance between MK6s.
    2. Perform calibration [cal_runs] times to get average time difference between MK6 and PC.
    3. Provide user with MK6 acme command to receive data.
    4. Create a UDP socket, bind, and increase receive buffer.
    5. Receive UDP packets, extract data, calculate delay, and store relevant information for analysis.
    6. Convert byte stream to dictionary data, unpickle it.
    7. Log the delay information along with other metrics like packet delivery rate, packet rate, and calibration time.

    ==============================================================
    """

    rx_coord = ut.GetCoords()
    rx_latitude = rx_coord[0]
    rx_longitude = rx_coord[1]

    print('\nRx Latitude: ' + str(rx_latitude) + '\n')
    print('Rx Longitude: ' + str(rx_longitude))

    tx_latitude = input("\nPlease enter Tx Latitude\n")
    tx_longitude = input("\nPlease enter Tx Longitude\n")

    rx_coord = (rx_latitude, rx_longitude)
    tx_coord = (tx_latitude, tx_longitude)

    dist = geopy.distance.geodesic(rx_coord, tx_coord).m

    print('\nDistance between MK6s: ' + str(dist) + ' meters')

    # Returns the averaged time difference between the GNSS (MK6) time and the current PC time
    rx_cal_time = ut.CalibrationDialogue(cal_runs)

    # Give user command to run on MK6
    interface = 'eth0'
    mk6_cmd = ("acme -R -P 111 -x " + interface + " -X " + mk6_addr + " -Y " + str(mk6_port) + " -d")
    print("\nRun this MK6 Command to receive data:")
    print(mk6_cmd)
    input("\nPress Enter to continue... ")

    # Create UDP socket
    rxsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Set large size for receieve buffer to account for connection discrepancies
    # This may be unneeded
    rxsock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 3_000_000)

    # Bind UDP socket to host and port
    rxsock.bind((mk6_addr, mk6_port))

    # set socket timeout
    rxsock.settimeout(10)
    
    # Set up some variables for later use
    pkt_cnt = pkt_tot
    delay = 0
    delay_arr = []

    print ('\nReceiving...\n')
        
    try:
        # Unlike the sender we count down the packets received from the packet number specified
        while pkt_cnt > 0:
                
            # Keep track of packets received
            pkt_cnt = pkt_cnt - 1

            # Receive pickled_predicted_labels from socket (address still unused)
            # 1024 works for now but may need to be modified in the future
            try:
                pickled_predicted_labels, address = rxsock.recvfrom(1024)
            except:
                break

            # Depickle the data from the transmitter
            predicted_labels = pickle.loads(pickled_predicted_labels)

            # Get packet rate from received data and remove data (as it is stored now)
            pkt_rate = predicted_labels["pkt_rate"]
            predicted_labels.popitem()

            # Get transmitter calibration from received data and remove data (as it is stored now)
            tx_cal_time = predicted_labels["calibration"]
            predicted_labels.popitem()
            
            # Calculate the overall calibration time of the system (time added by interfaces, ssh, etc.)
            cal_time = rx_cal_time + tx_cal_time 

            # Get transmitter time from received data and remove data (as it is stored now)
            tx_time = predicted_labels["time"]
            predicted_labels.popitem()

            # Compute/store the time between the transmitter/receiver omitting calibibration time
            rx_time = time.time()
            delay = rx_time - tx_time - cal_time
            delay_arr.append(abs(delay))
            
            print(predicted_labels)

        if(pkt_cnt == 0):
            print ('\nTotal packets received: %d\n' % (pkt_tot))
        else:
            # Example: 1000 pkts sent, 800 left in pkt_cnt => 1000 - 800 = 200 received  
            print ('\nTotal packets received: %d\n' % (pkt_tot - pkt_cnt))

        if(pkt_cnt > 0):
            print('Packets Dropped: '+ str(pkt_cnt) + '\n')

        # Add PDR for plotting
        # If pkt_cnt == 0 that means all packets were received -- so packet delivery rate is 100%
        if(pkt_cnt == 0):
            pdr = 100
        else:
            pdr = 100 * ((pkt_tot - pkt_cnt) / pkt_tot)

        # Add number of packets expected, pdr, pkt_rate, and total calibration time for plotting
        delay_arr.append(pkt_tot)
        delay_arr.append(abs(pdr))
        delay_arr.append(round(pkt_rate))
        delay_arr.append(abs(cal_time))
        delay_arr.append(dist)

        # Get the current time and convert it to a string for later file naming
        now = datetime.datetime.now()
        datestr = now.strftime("%Y_%m_%d_%H_%M_%S_%p") + ".txt"

        # Create a text log that contains pkt_cnt of packets, and prior delay_arr additions
        with open('./Logging/Delay/' + "delay_log_" + datestr, 'w') as fp:
            fp.write("\n".join(str(item) for item in delay_arr))
        
        rxsock.close()
    
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(1)
    except Exception as e:
        print ("Got exception:", e)
        raise

# String for help command
rx_str = ("""
====================
  ReceivePackets()
====================

Receive [pkt_tot] UDP packets from IPv4 IP [mk6_addr] on port [mk6_port] with [cal_runs] calibration runs.

Args:
    mk6_addr (str): The IP address of the MK6 radio.
    mk6_port (int): The port of the MK6 radio.
    pkt_tot  (int): The number of packets to receive.
    cal_runs (int): The number of calibration runs to undergo

Returns:
    None

==============================================================

TX                     RX
+---+                  +-------------------------------------+
|   | [acme at 5.9GHz] | +-----+ (mk6_addr, mk6_port) +----+ |
|   |----------------->| | MK6 |--------------------->| PC | |
|   | pkt_tot pkts     | +-----+ pkt_tot udp pkts     +----+ |
|   | as bytes         |  bytes                        dict  |
+---+                  +-------------------------------------+

1. Retrieve receiver coordinates from [log.txt] and calculate distance between MK6s.
2. Perform calibration [cal_runs] times to get average time difference between MK6 and PC.
3. Provide user with MK6 acme command to receive data.
4. Create a UDP socket, bind, and increase receive buffer.
5. Receive UDP packets, extract data, calculate delay, and store relevant information for analysis.
6. Convert byte stream to dictionary data, unpickle it.
7. Log the delay information along with other metrics like packet delivery rate, packet rate, and calibration time.

==============================================================
""")
