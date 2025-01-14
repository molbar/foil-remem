import uasyncio as asyncio
from micropython import const
from machine import Pin

TM1637_CMD1 = const(64)  # 0x40 data command
TM1637_CMD2 = const(192) # 0xC0 address command
TM1637_CMD3 = const(128) # 0x80 display control command
TM1637_DSP_ON = const(8) # 0x08 display on
TM1637_DELAY = const(10) # 10us delay between clk/dio pulses
TM1637_MSB = const(128)  # msb is the decimal point or the colon depending on your display

_SEGMENTS = bytearray(b'\x3F\x06\x5B\x4F\x66\x6D\x7D\x07\x7F\x6F\x77\x7C\x39\x5E\x79\x71\x3D\x76\x06\x1E\x76\x38\x55\x54\x3F\x73\x67\x50\x6D\x78\x3E\x1C\x2A\x76\x6E\x5B\x00\x40\x63')

class TM1637(object):
    """Library for quad 7-segment LED modules based on the TM1637 LED driver."""

    def __init__(self, clk, dio, brightness=7):
        self.clk = clk
        self.dio = dio
        if not 0 <= brightness <= 7:
            raise ValueError("Brightness out of range")
        self._brightness = brightness
        self.clk.init(Pin.OUT, value=0)
        self.dio.init(Pin.OUT, value=0)
        self._write_data_cmd()
        self._write_dsp_ctrl()

    async def _start(self):
        self.dio(0)
        await asyncio.sleep(TM1637_DELAY / 1000000)  # Convert microseconds to seconds for asyncio
        self.clk(0)
        await asyncio.sleep(TM1637_DELAY / 1000000)

    async def _stop(self):
        self.dio(0)
        await asyncio.sleep(TM1637_DELAY / 1000000)
        self.clk(1)
        await asyncio.sleep(TM1637_DELAY / 1000000)
        self.dio(1)

    async def _write_data_cmd(self):
        await self._start()
        await self._write_byte(TM1637_CMD1)
        await self._stop()

    async def _write_dsp_ctrl(self):
        await self._start()
        await self._write_byte(TM1637_CMD3 | TM1637_DSP_ON | self._brightness)
        await self._stop()

    async def _write_byte(self, b):
        for i in range(8):
            self.dio((b >> i) & 1)
            await asyncio.sleep(TM1637_DELAY / 1000000)  # Convert microseconds to seconds for asyncio
            self.clk(1)
            await asyncio.sleep(TM1637_DELAY / 1000000)
            self.clk(0)
            await asyncio.sleep(TM1637_DELAY / 1000000)
        self.clk(0)
        await asyncio.sleep(TM1637_DELAY / 1000000)
        self.clk(1)
        await asyncio.sleep(TM1637_DELAY / 1000000)
        self.clk(0)
        await asyncio.sleep(TM1637_DELAY / 1000000)

    async def brightness(self, val=None):
        """Set the display brightness 0-7."""
        if val is None:
            return self._brightness
        if not 0 <= val <= 7:
            raise ValueError("Brightness out of range")

        self._brightness = val
        await self._write_data_cmd()
        await self._write_dsp_ctrl()

    async def write(self, segments, pos=0):
        """Display up to 6 segments moving right from a given position."""
        if not 0 <= pos <= 5:
            raise ValueError("Position out of range")
        await self._write_data_cmd()
        await self._start()

        await self._write_byte(TM1637_CMD2 | pos)
        for seg in segments:
            await self._write_byte(seg)
        await self._stop()
        await self._write_dsp_ctrl()

    async def show(self, string, colon=False):
        segments = self.encode_string(string)
        if len(segments) > 1 and colon:
            segments[1] |= 128
        await self.write(segments[:4])

    async def scroll(self, string, delay=250):
        segments = string if isinstance(string, list) else self.encode_string(string)
        data = [0] * 8
        data[4:0] = list(segments)
        for i in range(len(segments) + 5):
            await self.write(data[0+i:4+i])
            await asyncio.sleep(delay / 1000)  # Convert milliseconds to seconds

    def encode_string(self, string):
        # Convert string to segments (as you defined before)
        segments = bytearray(len(string))
        for i in range(len(string)):
            segments[i] = self.encode_char(string[i])
        return segments

    def encode_char(self, char):
        # Encoding characters to segments as you defined
        o = ord(char)
        if o == 32:
            return _SEGMENTS[36] # space
        if o == 42:
            return _SEGMENTS[38] # star/degrees
        if o == 45:
            return _SEGMENTS[37] # dash
        if o >= 65 and o <= 90:
            return _SEGMENTS[o-55] # uppercase A-Z
        if o >= 97 and o <= 122:
            return _SEGMENTS[o-87] # lowercase a-z
        if o >= 48 and o <= 57:
            return _SEGMENTS[o-48] # 0-9
        raise ValueError("Character out of range: {:d} '{:s}'".format(o, chr(o)))
    
    def hex(self, val):
        """Display a hex value 0x0000 through 0xffff, right aligned."""
        string = '{:04x}'.format(val & 0xffff)
        self.write(self.encode_string(string))

    def number(self, num):
        """Display a numeric value -999 through 9999, right aligned."""
        # limit to range -999 to 9999
        num = max(-999, min(num, 9999))
        string = '{0: >4d}'.format(num)
        self.write(self.encode_string(string))

    def numbers(self, num1, num2, colon=True):
        """Display two numeric values -9 through 99, with leading zeros
        and separated by a colon."""
        num1 = max(-9, min(num1, 99))
        num2 = max(-9, min(num2, 99))
        segments = self.encode_string('{0:0>2d}{1:0>2d}'.format(num1, num2))
        if colon:
            segments[1] |= 0x80 # colon on
        self.write(segments)

    def temperature(self, num):
        if num < -9:
            self.show('lo') # low
        elif num > 99:
            self.show('hi') # high
        else:
            string = '{0: >2d}'.format(num)
            self.write(self.encode_string(string))
        self.write([_SEGMENTS[38], _SEGMENTS[12]], 2) # degrees C

    def show(self, string, colon=False):
        segments = self.encode_string(string)
        if len(segments) > 1 and colon:
            segments[1] |= 128
        self.write(segments[:4])

    async def scroll(self, string, delay=250):
        segments = string if isinstance(string, list) else self.encode_string(string)
        data = [0] * 8
        data[4:0] = list(segments)
        for i in range(len(segments) + 5):
            await self.write(data[0+i:4+i])
            await asyncio.sleep(delay / 1000)  # Convert milliseconds to seconds



class TM1637Decimal(TM1637):
    """Library for quad 7-segment LED modules based on the TM1637 LED driver.

    This class is meant to be used with decimal display modules (modules
    that have a decimal point after each 7-segment LED).
    """

    def encode_string(self, string):
        """Convert a string to LED segments.

        Convert an up to 4 character length string containing 0-9, a-z,
        space, dash, star and '.' to an array of segments, matching the length of
        the source string."""
        segments = bytearray(len(string.replace('.','')))
        j = 0
        for i in range(len(string)):
            if string[i] == '.' and j > 0:
                segments[j-1] |= TM1637_MSB
                continue
            segments[j] = self.encode_char(string[i])
            j += 1
        return segments

    





