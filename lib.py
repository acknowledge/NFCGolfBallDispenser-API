#!/usr/bin/env python

# THIS METHOD IS PART OF THE SMARTCARD.UTIL PACKAGE

"""smartcard.util package

__author__ = "http://www.gemalto.com"

Copyright 2001-2012 gemalto
Author: Jean-Daniel Aussel, mailto:jean-daniel.aussel@gemalto.com

This file is part of pyscard.

pyscard is free software; you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or
(at your option) any later version.

pyscard is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with pyscard; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""


PACK = 1
HEX = 2
UPPERCASE = 4
COMMA = 8

def toHexString(bytes=[], format=0):
    """Returns an hex string representing bytes

        bytes:  a list of bytes to stringify,
                    e.g. [59, 22, 148, 32, 2, 1, 0, 0, 13]
        format: a logical OR of
                COMMA: add a comma between bytes
                HEX: add the 0x chars before bytes
                UPPERCASE: use 0X before bytes (need HEX)
                PACK: remove blanks

        example:
        bytes = [ 0x3B, 0x65, 0x00, 0x00, 0x9C, 0x11, 0x01, 0x01, 0x03 ]

        toHexString(bytes) returns  3B 65 00 00 9C 11 01 01 03

        toHexString(bytes, COMMA) returns  3B, 65, 00, 00, 9C, 11, 01, 01, 03

        toHexString(bytes, HEX) returns
            0x3B 0x65 0x00 0x00 0x9C 0x11 0x01 0x01 0x03

        toHexString(bytes, HEX | COMMA) returns
            0x3B, 0x65, 0x00, 0x00, 0x9C, 0x11, 0x01, 0x01, 0x03

        toHexString(bytes, PACK) returns  3B6500009C11010103

        toHexString(bytes, HEX | UPPERCASE) returns
            0X3B 0X65 0X00 0X00 0X9C 0X11 0X01 0X01 0X03

        toHexString(bytes, HEX | UPPERCASE | COMMA) returns
            0X3B, 0X65, 0X00, 0X00, 0X9C, 0X11, 0X01, 0X01, 0X03
    """

    from string import rstrip

    for byte in tuple(bytes):
        pass

    if type(bytes) is not list:
        raise TypeError('not a list of bytes')

    if bytes == None or bytes == []:
        return ""
    else:
        pformat = "%-0.2X"
        if COMMA & format:
            pformat = pformat + ","
        pformat = pformat + " "
        if PACK & format:
            pformat = rstrip(pformat)
        if HEX & format:
            if UPPERCASE & format:
                pformat = "0X" + pformat
            else:
                pformat = "0x" + pformat
        return rstrip(rstrip(
                reduce(lambda a, b: a + pformat % ((b + 256) % 256),
                        [""] + bytes)), ',')