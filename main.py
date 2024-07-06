'''
Jonah Duncan, 04/11/24 - 05/30/24, CV2X Communication Program
'''
import sys
from operator import*

# Ignore warnings here -- importing self-made packages
import transmit as tx
import receive as rx
import plot as pd

if __name__ == '__main__':
    # This series of logic takes information entered into the terminal after 'python3 main.py' and uses it as the
    # arguments in this programs functions (with the function depending on the first string after ''.py)
    try:
        if sys.argv[1] == "tx":
            try:
                mk6_addr = sys.argv[2]
                mk6_port = int(sys.argv[3])
                pkt_rate = int(sys.argv[4])
                num_pkts = int(sys.argv[5])
                cal_runs = int(sys.argv[6])
                tx.TransmitPackets(mk6_addr, mk6_port, pkt_rate, num_pkts, cal_runs)
            except:
                print(tx.tx_str)
                sys.exit(1)
        elif sys.argv[1] == "rx":
            try:
                mk6_addr = sys.argv[2]
                mk6_port = int(sys.argv[3])
                num_pkts = int(sys.argv[4])
                cal_runs = int(sys.argv[5])
                rx.ReceivePackets(mk6_addr, mk6_port, num_pkts, cal_runs)
            except:
                print(rx.rx_str)
        elif sys.argv[1] == "pd":
            try:
                name = sys.argv[2]
                pd.PlotData(name)
            except:
                print(pd.pd_str)
                sys.exit(1)
        else:
            print('\nEnter valid command: tx, rx, pd\n')
    except:
        print('\nEnter valid command: tx, rx, pd\n')
        sys.exit(1)