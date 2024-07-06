'''
Jonah Duncan, 04/11/24 - 05/30/24, CV2X Plot Tools
'''
import matplotlib.pyplot as plt
import seaborn as sns
from operator import*

def PlotData(name: str) -> None:
    """
    Plots named data from ./Logging/Delay/[name].txt. 

    Args:
        name (str): The name of the data to be plotted.

    Returns:
        None
            
    ==============================================================
            
    [1] Densitity Percentage
    
    [2] Histogram of Packet Delay with Density Plot
    [3] Delivered [pdr] of [pkt_num] perception packets over [dist] meters at 5.9GHz
    [4] Total calibration time: [cal_time] ms
    [5] Transmitter Packet Rate: [pkt_rate] packets/sec
    [6] Packet Delay (ms)
    [7] Average: [avg_delay]

            [2]
            [3]
        +---------+
        |         |
    [1] |         | [4] [5]
        |         |
        +---------+
            [6]
            [7]

    ==============================================================
    """

    # Use the start of the file name to find the file path
    path = name.split('_')[0]
    if(path == "delay"):
        full_path = './Logging/Delay/'+ name + ".txt"
    else:
        full_path = './Logging/'+ 'handling' + '.txt'
        print("Please enter a valid path/name")

    # Open file and read the contents as a list
    data_arr = []
    with open(full_path, 'r') as fp:
        for line in fp:

            # Remove the linebreak character from the current line
            x = line[:-1]

            # Scale/Absolute the delay time at the current line and add to the data_arr list
            if (path == "delay"):
                data_arr.append(abs(1000*float(x)))

    # Store data added onto delay_list by receiver and remove from data_arr list
    distance = data_arr.pop() / 1000
    cal_time = round(data_arr.pop(),1)
    pkt_rate = int(data_arr.pop() / 1000)
    pdr = data_arr.pop() / 1000
    sent_pkts = data_arr.pop() / 1000

    avg_delay = abs(sum(data_arr) / len(data_arr))

    # String logic for x-axis
    if(path == "delay"):
        plt_str = "Packet Delay"
    else:
        plt_str = "Please enter a valid path/name"

    # Arbitrarily set histogram bin length for sample sizes up to 1000
    bin_len = 30

    # Create a customized histogram with a density plot
    ax = sns.histplot(data_arr, bins=bin_len, kde=True, color='lightgreen', edgecolor='red', stat='percent')

    # Create second y-axis with invisible ticks to hold experiment information
    ax2 = ax.twinx()
    ax2.set_ylabel(('Total Calibration Time: ' + str(cal_time) + ' ms\nTransmitter Packet Rate: ' + str(pkt_rate) + ' packets/sec'), color = 'black',labelpad=-15)
    ax2.tick_params(right = False, labelcolor='white')
    
    # Add labels and title to histogram
    ax.set_xlabel(plt_str + ' (ms)\n' + '[Average: ' + str(round(avg_delay,1)) + ']')
    ax.set_ylabel('Density Percentage')
    plt.title('Histogram of ' + plt_str + ' with Density Plot\n[Delivered ' + str(pdr) + '%' ' of ' + str(round(sent_pkts)) + ' perception packets over ' + str(round(distance,1)) + ' meters at 5.9GHz]') 

    # Display the plot
    plt.show()

# String for help command
pd_str = ("""
==============
  PlotData()
==============

Plots named data from ./Logging/Delay/[name].txt.

Args:
    name (str): The name of the data to be plotted.

Returns:
    None
          
==============================================================
          
[1] Densitity Percentage
[2] Histogram of Packet Delay with Density Plot
[3] Delivered [pdr] of [pkt_num] perception packets over [dist] meters at 5.9GHz
[4] Total calibration time: [cal_time] ms
[5] Transmitter Packet Rate: [pkt_rate] packets/sec
[6] Packet Delay (ms)
[7] Average: [avg_delay]

        [2]
        [3]
    +---------+
    |         |
[1] |         | [4] [5]
    |         |
    +---------+
        [6]
        [7]

==============================================================
""")