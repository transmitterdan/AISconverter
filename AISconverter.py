#!/usr/bin/env python
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import socket
import sys
import time
import string

tdDefault = 0.1     # Default time between sent messages
tcpTimeout = 5.0    # Timeout for inactive TCP socket
tcpConnectTimeout = 60.0	# Wait 60 seconds for a connection then exit
Space = ' '
Equals = '='

def Str2Float (str, exc):
    result = float(Str2Str(str,exc))
    return result
    
def Str2Int (str, exc):
    result = int(Str2Str(str,exc))
    return result

def Str2Str (str, exc):
    result = ''.join(ch for ch in str if ch not in exc)
    return result

def Int2BString (value, length):
    ZeroOne = dict({0: '0', 1: '1'})
    index = length
    result = list((' ' * length)[:length])
    while (index > 0):
        result[index-1] = ZeroOne[divmod(value,2)[1]]
        value = value//2
        index=index-1

    result = result[0:length]
    return result

def BString2Int(bitlist):  # convert reversed bit string to int
    length = len(bitlist)
    index = 0
    value = 0
    while (index < length):
        value = value + Str2Int(bitlist[index],'')*pow(2,index)
        index = index + 1

    return value

def nmeaEncode(LineDict):
    Ignore = {'"'}
    #ais NMEA payload encoding
    payloadencoding = {0:'0',1:'1',2:'2',3:'3',4:'4',5:'5',6:'6',7:'7',8:'8',9:'9',10:':',11:';',
                       12:'<',13:'=',14:'>',15:'?',16:'@',17:'A',18:'B',19:'C',20:'D',21:'E',22:'F',23:'G',24:'H',
                       25:'I',26:'J',27:'K',28:'L',29:'M',30:'N',31:'O',32:'P',33:'Q',34:'R',
                       35:'S',36:'T',37:'U',38:'V',39:'W',40:'`',41:'a',42:'b',43:'c',44:'d',
                       45:'e',46:'f',47:'g',48:'h',49:'i',50:'j',51:'k',52:'l',53:'m',54:'n',
                       55:'o',56:'p',57:'q',58:'r',59:'s',60:'t',61:'u',62:'v',63:'w'}
    cog = Str2Float(LineDict["COURSE"],Ignore)
    mmsi = Str2Int(LineDict["MMSI"],Ignore)
    lat = Str2Float(LineDict["LAT"],Ignore)
    lon = Str2Float(LineDict["LON"],Ignore)
    speed = Str2Float(LineDict["SPEED"],Ignore)
    status = Str2Int(LineDict["STATUS"],Ignore)
    heading = Str2Int(LineDict["HEADING"],Ignore)
    MessageID = Int2BString(1,6)
    RepeatIndicator = Int2BString(0,2)
    UserID = Int2BString(mmsi,30)
    NavStatus = Int2BString(0,4)   # Underway under engine
    RotAIS = Int2BString(-128,8)   # default is "not-available"
    SOG = Int2BString(speed,10)    # We assume the speed in the data set is in 1/10 knot
    PosAccuracy = Int2BString(1,1)
    Longitude = Int2BString(int(lon*600000),28)
    Latitude = Int2BString(int(lat*600000),27)
    COG = Int2BString(int(cog*10),12)
    Heading = Int2BString(heading,9)
    TimeStamp = Int2BString(60,6)  # not available
    Mi = Int2BString(0,2)
    Spare = Int2BString(0,3)
    RAIM = Int2BString(0,1)
    CommStat = Int2BString(0,19)

    BigString = MessageID
    BigString = BigString+RepeatIndicator
    BigString = BigString+UserID
    BigString = BigString+NavStatus
    BigString = BigString+RotAIS
    BigString = BigString+SOG
    BigString = BigString+PosAccuracy
    BigString = BigString+Longitude
    BigString = BigString+Latitude
    BigString = BigString+COG
    BigString = BigString+Heading
    BigString = BigString+TimeStamp
    BigString = BigString+Mi
    BigString = BigString+Spare
    BigString = BigString+RAIM
    BigString = BigString+CommStat

            
    intChars = list(range(0,28))
    BitPositions = [5,4,3,2,1,0]
    for chindex in range(0,28):
        StrVal = [BigString[index] for index in BitPositions]
        intChars[chindex] = BString2Int(StrVal)
        for idx in [0,1,2,3,4,5]:
            BitPositions[idx] = BitPositions[idx]+6
            
    # Now intChars contains the encoded bits for the AIS string
    aisnmea = 'AIVDM,1,1,,A,'
    for chindex in range(0,28):
        aisnmea = aisnmea + payloadencoding[intChars[chindex]]

    aisnmea = aisnmea + ',O'
    # Now we have the NMEA payload in aisnmea

    checksum = 0
    for chindex in range(0,len(aisnmea)):
        checksum = checksum ^ ord(aisnmea[chindex])
    aisnmea = '!' + aisnmea + '*' + '{:02x}'.format(checksum)
    return aisnmea

def udp(UDP_IP, UDP_PORT, filename, delay):
    print(['UDP target IP:', UDP_IP])
    print(['UDP target port:', str(UDP_PORT)])
    sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP
    f = open(filename, 'r')
    print("Type Ctrl-C to exit...")
    count = 0
    while True :
        try:
            LineText = f.readline()
            if len(LineText) < 1:
                f.close()
                sock.close()
                return True

            LineDict = {}
            elements = LineText.rstrip().split(Space)
            for elem in elements:
                b = elem.replace('"','').split(Equals)
                name = b[0]
                LineDict[name] = b[1]
                

            mess = nmeaEncode(LineDict)
	    #    print(mess)
            mess = mess.strip()
            mess = mess + u"\r\n"
            sock.sendto(mess.encode("utf-8"),(UDP_IP, UDP_PORT))
            time.sleep(delay)
        except KeyboardInterrupt:
            f.close()
            sock.close()
            return True
        except Exception as msg:
            print(msg)
            f.close()
            sock.close()
            return False

def tcp(TCP_IP, TCP_PORT, filename, delay):
    if TCP_IP == None:
        TCP_IP = socket.gethostname()

    server_address = (TCP_IP, TCP_PORT)

#    print(['TCP target IP:%s:%d', server_address])
#    print(['TCP target port:', str(TCP_PORT)])
    lsock = socket.socket(socket.AF_INET, # Internet
                          socket.SOCK_STREAM) # TCP
    lsock.settimeout(tcpConnectTimeout)
    try:
        lsock.bind(server_address)
        lsock.listen(1)
        print(["Server is waiting up to " + repr(tcpConnectTimeout) + "S for a connection at:", server_address]);
        conn, addr = lsock.accept()
    except socket.error as msg:
        print(msg)
        lsock.close()
        return False

    print(['Connecting to:', addr]);
    f = open(filename, 'r')
    print("Type Ctrl-C to exit...")
    while True:
        try:
            LineText = f.readline()
            if len(LineText) < 1:
                f.close()
                conn.close()
                lsock.close()
                return True

            LineDict = {}
            elements = LineText.rstrip().split(Space)
            for elem in elements:
                b = elem.replace('"','').split(Equals)
                name = b[0]
                LineDict[name] = b[1]

            mess = nmeaEncode(LineDict)
    #        print(mess)
            mess = mess.strip()
            mess = mess + u"\r\n"
            conn.send(mess.encode("utf-8"))
            time.sleep(delay)
        except KeyboardInterrupt:
            f.close()
            conn.close()
            lsock.close()
            return True
        except Exception as msg:
            print(msg)
            f.close()
            conn.close()
            lsock.close()
            return False

def usage():
    print("USAGE:")
    print("[python] AISconverter.py InputFile IP_Address Port# [Sleep time [TCP]]")
    print("Sleep time is the delay in seconds between AIS messages sent.")
    print("Sleep time defaults to 0.1 seconds")
    print("If three letter string after sleep time is TCP then TCP/IP packets are sent")
    print("else UDP packets are sent.")
    return

if len(sys.argv) < 4:
    print(sys.argv)
    usage()
    sys.exit()

if len(sys.argv) > 4:
    td = float(sys.argv[4])
else:
    td = tdDefault        # default time between messages

if len(sys.argv) > 5:
    mode = sys.argv[5]
else:
    mode = "UDP"

rCode = False

if mode.upper() == "UDP":
    rCode = udp(sys.argv[2], int(sys.argv[3]), sys.argv[1], td)

if mode.upper() == "TCP":
    rCode = tcp(sys.argv[2], int(sys.argv[3]),sys.argv[1], td)

if rCode == True:
    print("Exiting cleanly.")
else:
    print("Something went wrong, exiting.")

sys.exit()
