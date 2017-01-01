# AISconverter
Convert data in a text file to NMEA AIS data usable by OpenCPN

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.
   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

USAGE: python AISconverter.py InputFile --dest=IP_Address --port=Port# [--sleep=Sleep time [--TCP | --UDP]]
    
    Sleep time is the delay in seconds between AIS messages sent.
    
    IP_Address is IP of destination for UDP mode. Default is 'localhost'
    
    Sleep time defaults to 0.1 seconds
    
    If three letter string after sleep time is TCP then TCP/IP packets are sent
    
    else UDP packets are sent.
    
