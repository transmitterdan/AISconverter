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

#	Usage: Create a text data file containing key AIS data.  Presently the program
#	only accepts 3 types of AIS messages (1, 18 & 24).  Message type 1 is for
#	class A vessel position report.  For Type 1 we only indicate channel A.  Maybe
#	later this will be changed to get the channel from the data file.  Type 18 is
#	for class B vessel position report.  Type 24 is for class B vessel static
#	information.  There are 2 subtypes of a type 24 message (A and B or 0 and 1).
#	The first type is mainly for the vessel name.  The second type is for call
#	sign and vessel type.  Both subtypes are currently supported.  See example file
#	sample.txt for examples of each type of message.   For help just run the
#	script as 'python AISconverter' without arguments.  It will print out a little
#	usage help.  The most common example of arguments would be:
#       python AISconverter.py sample.txt localhost 10110 .1 UDP
#           sample.txt is the name of the data file to read
#	        localhost is the IP address of the computer running the script
#           10110 is the normal port OpenCPN uses to receive UDP NMEA data
#           .1 means delay 100mS between messages
#           UDP means make a UDP connection to the client (TCP is also supported)
#   If a data file name is not provided then it will read from STDIN (or a pipe).

import socket
import sys
import os
import time
import string
import getopt

# default argument values
port = 10110    # Default port
td = 0.1        # Default time between sent messages is 100mS
mode = "UDP"    # Default mode is UDP
dest = "localhost" # Default destination IP address

tcpTimeout = 5.0    # Timeout for inactive TCP socket
tcpConnectTimeout = 60.0	# Wait 60 seconds for a connection then exit
Space = ' '
Equals = '='

#ais NMEA payload encoding
payloadencoding = {0:'0',1:'1',2:'2',3:'3',4:'4',5:'5',6:'6',7:'7',8:'8',9:'9',10:':',11:';',
                   12:'<',13:'=',14:'>',15:'?',16:'@',17:'A',18:'B',19:'C',20:'D',21:'E',22:'F',23:'G',24:'H',
                   25:'I',26:'J',27:'K',28:'L',29:'M',30:'N',31:'O',32:'P',33:'Q',34:'R',
                   35:'S',36:'T',37:'U',38:'V',39:'W',40:'`',41:'a',42:'b',43:'c',44:'d',
                   45:'e',46:'f',47:'g',48:'h',49:'i',50:'j',51:'k',52:'l',53:'m',54:'n',
                   55:'o',56:'p',57:'q',58:'r',59:'s',60:'t',61:'u',62:'v',63:'w'}

# Sixbit ASCII encoding
sixbitencoding = {'@':0,'A':1,'B':2,'C':3,'D':4,'E':5,'F':6,'G':7,'H':8,'I':9,'J':10,'K':11,'L':12,'M':13,'N':14,'O':15,
                  'P':16,'Q':17,'R':18,'S':19,'T':20,'U':21,'V':22,'W':23,'X':24,'Y':25,'Z':26,'[':27,'\\':28,']':29,'^':30,'_':31,
                  ' ':32,'!':33,'"':34,'#':35,'$':36,'%':37,'&':38,'\'':39,'(':40,')':41,'*':42,'+':43,',':44,'-':45,'.':46,'/':47,
                  '0':48,'1':49,'2':50,'3':51,'4':52,'5':53,'6':54,'7':55,'8':56,'9':57,':':58,';':59,'<':60,'=':61,'>':62,'?':63}

def Str2Float (str, exc):
    result = float(Str2Str(str,exc))
    return result
    
def Str2Int (str, exc):
    result = int(Str2Str(str,exc))
    return result

def Str2Six (str, length):
    result = []
    for letter in str:
        result = result + Int2BString(sixbitencoding[letter],6)

    while len(result) < length:
        result = result + Int2BString(sixbitencoding['@'],6)

    result = result[0:length]
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

def NMEAencapsulate(BigString,sixes):
    capsule = ''
    intChars = list(range(0,sixes))
    BitPositions = [5,4,3,2,1,0]
    for chindex in range(0,sixes):
        StrVal = [BigString[index] for index in BitPositions]
        intChars[chindex] = BString2Int(StrVal)
        for idx in [0,1,2,3,4,5]:
            BitPositions[idx] = BitPositions[idx]+6
            
    # Now intChars contains the encoded bits for the AIS string
    for chindex in range(0,sixes):
        capsule = capsule + payloadencoding[intChars[chindex]]

    # Now we have the NMEA payload in capsule
    return capsule

def nmeaEncode(LineDict):
    Ignore = {'"'}
    if LineDict["TYPE"] == "1":
        # This is a Class A position update message
        cog = Str2Float(LineDict["COURSE"],Ignore)
        mmsi = Str2Int(LineDict["MMSI"],Ignore)
        lat = Str2Float(LineDict["LAT"],Ignore)
        lon = Str2Float(LineDict["LON"],Ignore)
        speed = Str2Float(LineDict["SPEED"],Ignore)
        status = Str2Int(LineDict["STATUS"],Ignore)
        heading = Str2Int(LineDict["HEADING"],Ignore)

        tStamp = LineDict["TIMESTAMP"]
        tSecond = Str2Int(tStamp[len(tStamp)-2:len(tStamp)],Ignore)
        MessageID = Int2BString(Str2Int(LineDict["TYPE"],Ignore),6)
        RepeatIndicator = Int2BString(0,2)
        UserID = Int2BString(mmsi,30)
        NavStatus = Int2BString(status,4)
        RotAIS = Int2BString(-128,8)   # default is "not-available"
        SOG = Int2BString(speed,10)    # We assume the speed in the data set is in 1/10 knot
        PosAccuracy = Int2BString(1,1)
        Longitude = Int2BString(int(lon*600000),28)
        Latitude = Int2BString(int(lat*600000),27)
        COG = Int2BString(int(cog*10),12)
        Heading = Int2BString(heading,9)
        TimeStamp = Int2BString(tSecond,6)
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
        capsule = NMEAencapsulate(BigString, 28)
        aisnmea = 'AIVDM,1,1,,A,'+ capsule + ',O'

    if LineDict["TYPE"] == "18":
        # This is a Class B position update message
        MessageID = Int2BString(Str2Int(LineDict["TYPE"],Ignore),6)
        RepeatIndicator = Int2BString(0,2)
        MMSI = Int2BString(Str2Int(LineDict["MMSI"],Ignore),30)
        Spare1 = Int2BString(0,8)
        Channel = LineDict["CHANNEL"]

        sog = Str2Float(LineDict["SPEED"],Ignore)
        SOG = Int2BString(sog,10)

        PosAccuracy = Int2BString(1,1)

        lon = Str2Float(LineDict["LON"],Ignore)
        Longitude = Int2BString(int(lon*600000),28)

        lat = Str2Float(LineDict["LAT"],Ignore)
        Latitude = Int2BString(int(lat*600000),27)

        cog = Str2Float(LineDict["COURSE"],Ignore)
        COG = Int2BString(int(cog*10),12)

        heading = Str2Int(LineDict["HEADING"],Ignore)
        Heading = Int2BString(heading,9)

        tStamp = LineDict["TIMESTAMP"]
        tSecond = Str2Int(tStamp[len(tStamp)-2:len(tStamp)],Ignore)
        TimeStamp = Int2BString(tSecond,6)

        Spare2 = Int2BString(0,2)

        State = Int2BString(393222,27)


        BigString = MessageID
        BigString = BigString+RepeatIndicator
        BigString = BigString+MMSI+Spare1+SOG+PosAccuracy+Longitude+Latitude+COG+Heading+TimeStamp+Spare2
        BigString = BigString+State
        capsule = NMEAencapsulate(BigString, 28)
        aisnmea = 'AIVDM,1,1,,' + Channel +','+ capsule + ',O'

    if LineDict["TYPE"] == "24":
        # This is a Class B Static Data Report
        MessageID = Int2BString(Str2Int(LineDict["TYPE"],Ignore),6)
        RepeatIndicator = Int2BString(0,2)
        MMSI = Int2BString(Str2Int(LineDict["MMSI"],Ignore),30)
        part_no = Str2Int(LineDict["PART_NO"],Ignore)
        PartNumber = Int2BString(part_no,2)
        Channel = LineDict["CHANNEL"]
        if part_no == 0:
            Name = Str2Six(LineDict["SHIP_NAME"],120)
            Spare = Int2BString(0,8)
            BigString = MessageID+RepeatIndicator+MMSI+PartNumber+Name+Spare
            capsule = NMEAencapsulate(BigString, 28)

        if part_no == 1:
            Type = Int2BString(Str2Int(LineDict["SHIP_TYPE"],Ignore),8)
            VendorID = Int2BString(0,42)
            CallSign = Str2Six(LineDict["CALL_SIGN"],42)
            Dim = Int2BString(0,30)
            Spare = Int2BString(0,6)
            BigString = MessageID+RepeatIndicator+MMSI+PartNumber+Type+VendorID+CallSign+Dim+Spare
            capsule = NMEAencapsulate(BigString, 28)

        aisnmea = 'AIVDM,1,1,,' + Channel + ',' + capsule + ',O'

    checksum = 0
    for chindex in range(0,len(aisnmea)):
        checksum = checksum ^ ord(aisnmea[chindex])
    aisnmea = '!' + aisnmea + '*' + '{:02X}'.format(checksum)
    return aisnmea

def parse_line(f):

    LineDict = {}
    LineText = f.readline()

    if len(LineText)==0:
        raise EOFError

    keyFound = False
    key = ""
    for Chars in LineText:
        if not(keyFound):
            if Chars == '=':
                keyFound = True
                key = key.strip()
                start = False
                finish = False
                value = ""
                continue
            else:
                key = key+Chars
                continue

        if not(start):
            if Chars == '"':
                start = True
                continue
            else:
                continue

        if not(finish) & start:
            if Chars == '"':
                finish = True;

        if not(finish) & start:
            value = value + Chars

        if start & finish:
            LineDict[key] = value;
            keyFound = False
            key = ""
    return LineDict

def udp(UDP_IP, UDP_PORT, f, delay):
    print(['UDP target IP:', UDP_IP])
    print(['UDP target port:', str(UDP_PORT)])
    sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP
    print("Type Ctrl-C to exit...")
    count = 0
    while True :
        try:
            LineDict = parse_line(f)
            if LineDict:
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

        except EOFError:
            f.close()
            sock.close()
            return True

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            f.close()
            sock.close()
            return False

def tcp(TCP_IP, TCP_PORT, f, delay):
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

    print(['Connected via TCP to:', addr]);
    print("Type Ctrl-C to exit...")
    while True:
        try:
            LineDict = parse_line(f)
            if LineDict:
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

        except EOFError:
            f.close()
            lsock.close()
            return True

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            f.close()
            conn.close()
            lsock.close()
            return False

def usage():
    print("Usage: python AISconverter.py [OPTION]... [FILE]...")
    print("Convert plain text in FILE to NMEA AIS format data and send out via IP address/port.")
    print("")
    print("-d, -dest=IP_Address        destination IP address.")
    print("-h, --help                  this message.")
    print("-p, --port=#                destination port number.")
    print("                            Any valid port is accepted.")
    print("-s, --sleep=#.#             sleep time between packets.")
    print("                            default is 0.1 seconds.")
    print("-t, --TCP                   create TCP connection.")
    print("-u, --UDP                   use connectionless UDP.")
    print("                            UDP is default if no connection type specified.")
    print("")
    print("If no FILE is given then default is to read input text from STDIN.")
    return

options, remainder = getopt.gnu_getopt(sys.argv[1:], 'hd:p:s:ut', ['help','dest=','port=','sleep=','UDP','TCP'])

for opt, arg in options:
    if opt in ('-d', '--dest'):
        dest = arg
    elif opt in ('-p', '--port'):
        port = Str2Int(arg,'')
    elif opt in ('-s', '--sleep'):
        td = Str2Float(arg,'')
    elif opt in ('-u', '--UDP'):
        mode = 'UDP'
    elif opt in ('-t', '--TCP'):
        mode = 'TCP'
    elif opt in ('-h', '--help'):
        usage()
        sys.exit()

if remainder:
    file = open(remainder[0],'r')
else:
    file = sys.stdin

#if len(sys.argv) < 4:
#    print(sys.argv)
#    usage()
#    sys.exit()

#if len(sys.argv) > 4:
#    td = float(sys.argv[4])
#else:
#    td = tdDefault        # default time between messages

#if len(sys.argv) > 5:
#    mode = sys.argv[5]
#else:
#    mode = "UDP"

rCode = False

if mode.upper() == "UDP":
    rCode = udp(dest,port,file,td)

if mode.upper() == "TCP":
    rCode = tcp(dest,port,file,td)

if rCode == True:
    print("Exiting cleanly.")
else:
    usage()
    print("Something went wrong, exiting.")

sys.exit()
