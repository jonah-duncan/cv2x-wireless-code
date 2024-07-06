'''
Jonah Duncan, 04/11/24 - 05/30/24, CV2X Transmission Tools
'''
import time
import socket
import sys
import pickle
from operator import*

# Ignore warnings here -- importing self-made packages
import utilities as ut

def TransmitPackets(mk6_addr: str, mk6_port: int, pkt_rate: int, pkt_tot: int, cal_runs: int) -> None:
    """
    Send [pkt_tot] UDP packets at [pkt_rate] pkts/s to IPv4 IP [mk6_addr] on port [mk6_port] with [cal_runs] calibration runs.

    Args:
        mk6_addr (str): The IP address of the MK6 radio.
        mk6_port (int): The port of the MK6 radio.
        pkt_rate (int): The number of packets per second to send to the MK6 radio.
        pkt_tot  (int): The number of packets to send. -1 sends packets forever.
        cal_runs (int): The number of calibration runs to undergo

    Returns:
        None

    ==============================================================

    TX                                                       RX
    +-------------------------------------+                  +---+
    | +----+ (mk6_addr, mk6_port) +-----+ | [acme at 5.9GHz] |   |
    | | PC |--------------------->| MK6 | |----------------->|   |
    | +----+ pkt_rate udp pkts/s  +-----+ | pkt_tot pkts     |   |
    |  dict                        bytes  | as bytes         |   |
    +-------------------------------------+                  +---+

    1. Set initial packet rate to [pkt_rate]
    2. Retrieve transmitter coordinates from [log.txt].
    3. Perform calibration [cal_runs] times to get average time difference between MK6 and PC.
    4. Provide user with MK6 acme command to transmit data.
    5. Create a UDP socket, bind, and set broadcast option.
    6. Pull dictionary data from [predicted_labels.txt] in [./Results/].
    7. Convert dictionary data into a byte array, pickle it.
    8. Send [pkt_tot] packets to [mk6_addr] at [mk6_port] with packet rate adjustment.

    ==============================================================
    """

    tx_coord = ut.GetCoords()
    tx_latitude = tx_coord[0]
    tx_longitude = tx_coord[1]

    print('\nTx Latitude: ' + str(tx_latitude) + '\n')
    print('Tx Longitude: ' + str(tx_longitude))

    # Period of packet generation, where a packet is what carries the perception data
    # Converts int to float
    PktPeriod = 1.0/pkt_rate

    # Time to sleep between packets
    sleeptime = PktPeriod

    # Returns the averaged time difference between the GNSS (MK6) time and the current PC time
    tx_cal_time = ut.CalibrationDialogue(cal_runs)

    # Give user command to run on MK6
    interface = 'eth0'
    mk6_cmd = ("acme -L " + str(mk6_port) + " -E -P 111 -x " + interface + " -d")
    print("\nRun this MK6 Command to transmit data:")
    print(mk6_cmd)
    input("\nPress Enter to continue... ")

    # Create UDP socket to host and port
    txsock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind to whatever port we can get our hands on (direct binding doesn't work here in my tests)
    txsock.bind(('', 50000)) 

    # Set just this socket level to broadcast
    txsock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # These can be used in the future possibly
    txsock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 3_000_000)
    txsock.settimeout(0.050)

    # Get time and set period to prime packet rate variables
    primed_time = time.time()
    primed_period = 1.0

    # Prime variables to time packets for limiting packet rate
    new_time = primed_time
    start_time = primed_time
    last_update_time = primed_time
    start_time = primed_time
    update_period = primed_period
    pkt_rate_period = primed_period

    # Initialise other variables
    start_pkt_cnt = 0
    pkt_cnt = 0
    sleep_time_arr = []
    sleep_time_avg = 0

    try:
        while (pkt_cnt < pkt_tot) or (pkt_tot == -1):
                        
            # This generates an empty byte array to be appended
            pktbuf = bytearray()

            # Converts Text file to dictionary
            predicted_labels = {}
            with open('./Results/predicted_labels.txt') as f:
                # Remove trailing whitespace with restrip
                # Split line into two parts using first occurance of whitespace as delimiter
                # First occurance of whitespace is key
                predicted_labels = dict(x.rstrip().split(None, 1) for x in f)

            # Add current PC time, calibration time, and packet rate to predicted_labels perception packet
            predicted_labels.update({"time": time.time(), "calibration": tx_cal_time, "pkt_rate": pkt_rate})

            # Convert dictionary to bytes using pickle.dumps()
            pktbuf = pickle.dumps(predicted_labels)
            
            # Print the type and value of the bytes object
            print(pktbuf)

            # The +1 here is to account for internal iteration
            print ('\nTotal packets transmitted: %d\n' % (pkt_cnt+1))

            # Transmit the packet to the MK6 via the socket
            txsock.sendto(pktbuf, (mk6_addr, mk6_port))

            # Increment packet numbers
            pkt_cnt = pkt_cnt + 1
            
            # Check if the time difference between the current and last update time is greater than the update period
            if (new_time - last_update_time > update_period):
                last_update_time = new_time

            # Keep adjusting sleep time to keep our rate to desired level, averaged over pkt_rate_period intervals
            # New time is updated here for above logic in next iteration
            new_time = time.time()
            error_time = (PktPeriod*(pkt_cnt - start_pkt_cnt) - (new_time - start_time))
            sleep_time = PktPeriod + error_time

            # If pkt_rate_period is exceeded reset start_pkt_cnt and start_time
            if (new_time - start_time > pkt_rate_period):
                start_time = new_time
                start_pkt_cnt = pkt_cnt
            
            # We can only sleep non-negative times so we force sleep_time to zero
            if sleep_time < 0:
                sleep_time = 0

            # Debugging to see packet rate adjustment
            sleep_time_arr.append(sleep_time)

            # Sleep between packets to keep to packet rate
            time.sleep(sleep_time)

        # Debugging to see packet rate adjustment
        if(len(sleep_time_arr) != 0):
            sleep_time_avg = abs(sum(sleep_time_arr) / len(sleep_time_arr))
        else:
            sleep_time_avg = 1.0
        print('Average Packet Rate: '+ str((1.0/sleep_time_avg)) + '\n')

        txsock.close()

    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(1)
    except Exception as e:
        print ("Got exception:", e)
        raise

# String for help command
tx_str = ("""
=====================
  TransmitPackets()
=====================

Send [pkt_tot] UDP packets at [pkt_rate] pkts/s to IPv4 IP [mk6_addr] on port [mk6_port] with [cal_runs] calibration runs.

Args:
    mk6_addr (str): The IP address of the MK6 radio.
    mk6_port (int): The port of the MK6 radio.
    pkt_rate (int): The number of packets per second to send to the MK6 radio.
    pkt_tot  (int): The number of packets to send. -1 sends packets forever.
    cal_runs (int): The number of calibration runs to undergo

Returns:
    None

==============================================================

TX                                                       RX
+-------------------------------------+                  +---+
| +----+ (mk6_addr, mk6_port) +-----+ | [acme at 5.9GHz] |   |
| | PC |--------------------->| MK6 | |----------------->|   |
| +----+ pkt_rate udp pkts/s  +-----+ | pkt_tot pkts     |   |
|  dict                        bytes  | as bytes         |   |
+-------------------------------------+                  +---+

1. Set initial packet rate to [pkt_rate]
2. Retrieve transmitter coordinates from [log.txt].
3. Perform calibration [cal_runs] times to get average time difference between MK6 and PC.
4. Provide user with MK6 acme command to transmit data.
5. Create a UDP socket, bind, and set broadcast option.
6. Pull dictionary data from [predicted_labels.txt] in [./Results/].
7. Convert dictionary data into a byte array, pickle it.
8. Send [pkt_tot] packets to [mk6_addr] at [mk6_port] with packet rate adjustment.

==============================================================
""")