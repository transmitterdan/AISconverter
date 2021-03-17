# AISconverter
Convert data in a text file to NMEA-0183 AIS data usable by ECDIS display
programs such as OpenCPN

This program reads a plain text file containing key/value pairs and converts each line into a validAIS NMEA-0183 message.  This is useful if you have voyage related data in plain text format and wish to see that data displayed in a navigation program such as OpenCPN or any other program that can display AIS ship data.  There are 4 types of AIS message this program understands.  Each type of message is encoded into the NMEA-0183 format and sent to a destination IP address as specified in the command line.

* **Special thanks to these online resources:**
   - <https://gpsd.gitlab.io/gpsd/NMEA.html>
   - <https://gpsd.gitlab.io/gpsd/AIVDM.html>
   - <https://opencpn.org>

   Consult the links above for more details about NMEA messages in general and
   typical data contained in AIS messages.

## USAGE:

``` 
   python AISconverter.py InputFile --dest=IP_Address --port=Port# [--sleep=Sleep time [--TCP | --UDP]]
```
   - IP_Address is the destination IP address for UDP connections.  For TCP connections the IP_Address is the address you wish the server to use.  Most commonly the server will be localhost or the URL of the host machine.  Clients will attempt to connect to this IP address.

   - Port# is the port number you wish to use.  The client must use this same number to make a connection.
   - Sleep time is the delay in seconds between AIS messages sent. Sleep time defaults to 0.1 seconds.
   - TCP indicates the program should act as a server and await connection.  We only allow one connection at a time.
   - UDP indicates the program will stream out messages to the specified IP address. No error is reported if the destination IP address is invalid or the messages to not make it to the destination.

Each NMEA message is formed by reading one line of the input file (possibly from STDIN) and forming the designated NMEA text string.  Then the message is transmitted.  This repeats until the end of file is reached.

Each line of the file is made up of KEY="VALUE" pairs separated by spaces.  All data for a single message must appear on one line.  The key values are case insensitive.  So, for example, type="5" and TYPE="5" are equivalent.  If you include the same key more than once in a line only the last key/value pair is retained.

* **Examples of each message type and required syntax:**

NOTE: ALL TEXT IN A GIVEN MESSAGE MUST BE ON ONE LINE IN THE TEXT FILE! HERE WE DESCRIBE EACH FIELD ON A SINGLE LINE AND GIVE A WORKING EXAMPELE OF EACH VALID MESSAGE TYPE.

Wherever possible, the program will provide a default value if a key/pair is missing. However, values may cause unexpected problems.  For example, MMSI and IMO numbers must be unique for each vessel.  So using the default for these may destroy previous data with the same MMSI or IMO.

* **Message descriptions**

### Message Type 1:

   - TYPE="1", mandatory message type
   - MMSI="367415981", optional - will default to 99999
   - STATUS="5", optional - will default to 0
   - SPEED="0", optional - will default to 0
   - LON="122.745400", optional - will default to 0
   - LAT="27.135410", optional - will default to 0
   - COURSE="113", optional - will default to 0
   - HEADING="30", optional - will default to 0
   - ROT="0", optional - will default to -128 (not available)
   - TIMESTAMP="2021-11-19T05:19:47", optional - will default to computer UTC time

```
TYPE="1" MMSI="367415981" STATUS="5" SPEED="0" LON="122.745400" LAT="27.135410" COURSE="113" HEADING="30" ROT="0" TIMESTAMP="2021-11-19T05:19:47"
```
### Message Type 5:

   - TYPE="5", mandatory message type
   - RepeatIndicator="3", optional - will default to "3" (do not repeat)
   - Channel="A", optional AIS channel - will default to "A"
   - MMSI="123446", optional MMSI - will default to "99999"
   - AISversion="0", optional - will default to "0"
   - ImoNumber="45634", optional - will default to "99999"
   - CallSign="WDE3241", optional - will default to "CALL"
   - VesselName="WIND WALKER", optional - will default to "SHIP_NAME"
   - ShipType="0", optional - will default to "0"
   - ToBow="15", optional distance to bow (meters) - will default to "99"
   - ToStern="15", optional distance to stern (meters) - will default to "99"
   - ToPort="5", optional distance to port (meters) - will default to "99"
   - ToStbd="1", optional distance to starboard (meters) - will default to "99"
   - FixType="0", optional - will defaulte to "0"
   - ETAmonth="6", optional - will default to "1" (January)
   - ETAday="7", optional - will default to "1"
   - ETAhour="20", optional - will default to "0" (midnight)
   - ETAmin="30", optional - will default to "0"
   - Draught="6", optional - will default to "99" (meters)
   - Dest="SF BAY", optional - will default to "NONE"

```
TYPE="5" RepeatIndicator="3" Channel="A" MMSI="123446" AISversion="0" ImoNumber="45634" CallSign="WDE3241" VesselName="WIND WALKER" ShipType="0" ToBow="15" ToStern="15" ToPort="5" ToStbd="1" FixType="0" ETAmonth="6" ETAday="7" ETAhour="20" ETAmin="30" Draught="6" Dest="SF BAY"
```
### Message Type 18:

   - TYPE="18", mandatory message type
   - MMSI="367415980", optional - will default to "99999"
   - SPEED="0", optional - will default to "0"
   - LON="121.745400", optional - will default to "0"
   - LAT="24.135410", optional - will default to "0"
   - COURSE="113", optional - will default to "0"
   - HEADING="30", optional - will default to "0"
   - CHANNEL="B", optional - will default to "A"
   - TIMESTAMP="2021-11-19T05:19:47", optional - will default to computer UTC time

```
TYPE="18" MMSI="367415980" SPEED="0" LON="121.745400" LAT="24.135410" COURSE="113" HEADING="30" CHANNEL="B" TIMESTAMP="2021-11-19T05:19:47"
```

NOTE: Message 24 has 2 sub-types known as "Parts". These should appear in the text file
in sequential lines.  The MMSI number tells us that the data belong to a common vessel.
Therefore, MMSI should be identical in each part for same vessel.

### Message Type 24 (first part):

   - TYPE="24", mandatory message type
   - MMSI="367415980", optional - will default to "99999"
   - PART_NO="0", mandatory
   - CHANNEL="A", optional - will default to "A"
   - SHIP_NAME="LOLLYPOP", - will default to "NAME"

### Message Type 24 (second part):

   - TYPE="24", mandatory message type
   - MMSI="367415980", optional - will default to "99999"
   - PART_NO="1", mandatory
   - CHANNEL="A", optional - will default to "A"
   - SHIP_TYPE="8", optional - will default to "0"
   - CALL_SIGN="WDE9000", optional - will default to "CALL"

```
TYPE="24" MMSI="367415980" CHANNEL="A" SHIP_NAME="LOLLYPOP"
TYPE="24" MMSI="367415980" PART_NO="1" CHANNEL="A" SHIP_TYPE="8" CALL_SIGN="WDE9000"
```

Use the https://github.com/transmitterdan/AISconverter/issues link to ask questions or report problems.
