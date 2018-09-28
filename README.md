# Get F5 VPN for MacOS Troubleshooting Data
Generate and collect client (MacOS) and server (BIG-IP) side F5 VPN for MacOS troubleshooting data.
 
  - Data collected on MacOS: pcap of initial connection, long running pcap files, logs (~/Library/Logs/F5Networks/), MacOS systems logs
  - Data collected on BIG-IP: pcap of initial connection, long running pcap files, logs (/var/log/), bbrdump, tmctl ppp stats (beofore and after pcaps), qkview

# How-To
1. Put the respective scripts on the MacOS client and BIG-IP server where data will be collected from
2. Edit the scripts and customize the parameters at the top, under heading '### Customize these parameters ###'
3. Start the programs simultaneously from cli: python /path/to/script 
  > The MacOS script will prompt for the user's password as elevated rights are required for several commands contained within
4. On the MacOS client, start an F5 VPN connection and once connected press Enter on both programs to stop the INITIAL connection captures and to start the LONG RUNNING captures
  > Editing the scripts and setting parameter PAUSE to True will cause the program to halt after stopping the INITIAL capture and before starting the LONG RUNNING capture, requiring enduser to press Enter to resume program
5. After desired period of time runnnig the program, press Enter to stop the LONG RUNNING capture and end the program
6. The end result will be compressed troubleshooting files
