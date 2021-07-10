# SPDX-FileCopyrightText: 2021 Diego Elio Pettenò
#
# SPDX-License-Identifier: 0BSD

import click
import serial

import structs


class HVACEmu:

    _serial: serial.Serial
    _last_packet: bytes = b""

    def __init__(self, serial_port: str) -> None:
        self._serial = serial.Serial(serial_port, baudrate=104, timeout=0.3)

    def loop(self):
        buffer = b""
        while True:
            newpkt = self._serial.read(6)
            if not newpkt:
                buffer = b""
            else:
                buffer += newpkt

            if len(buffer) == 6:
                self.process(buffer)
                buffer = b""

            assert len(buffer) < 6

    def process(self, buffer: list[int]) -> None:
        if buffer != self._last_packet:            
            parsed = structs.HVAC_CONTROL.parse(buffer)
            print(parsed)
            self._last_packet = buffer

        if buffer[:5] == b"\x94\x00\x00\x00\x00":
            # buffer[1] & 0x20 => if present, vane control and power speed disabled
            # buffer[1] & 0x01 => heat pump present

            # message = b'\xd1\x21\xe2\x00\x00'
            message = b"\xd1\x21\xe0\x00\x00"
        else:
            message = b"\x88\x26\x00\x00\x00"
        message += bytes([structs.calculate_checksum(message)])

        self._serial.write(message)
        pkt2 = b""
        while len(pkt2) < 6:
            pkt2 += self._serial.read(1)
        if pkt2 != message:
            print(pkt2, message)


@click.command()
@click.argument(
    "serial-port", type=click.Path(dir_okay=False, file_okay=True, writable=True)
)
def main(serial_port: str) -> None:

    emu = HVACEmu(serial_port)
    emu.loop()


if __name__ == "__main__":
    main()
