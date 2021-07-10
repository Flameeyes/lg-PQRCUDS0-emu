# SPDX-FileCopyrightText: 2021 Diego Elio Pettenò
#
# SPDX-License-Identifier: 0BSD

import asyncio
import dataclasses
import datetime

import aioconsole
import click
import serial

import structs


class PanelEmu:

    _serial: serial.Serial
    _next_settings: structs.Settings
    _last_settings: structs.Settings
    _period: datetime.timedelta

    def __init__(self, serial_port: str, period: datetime.timedelta) -> None:
        self._serial = serial.Serial(serial_port, baudrate=104, timeout=1.5)
        self._last_settings = self._next_settings = structs.Settings()
        self._period = period

    async def bus_loop(self):
        while True:
            await asyncio.sleep(self._period.total_seconds())
            if self._last_settings != self._next_settings:
                packet = self._next_settings.to_packet(changed=True)
                self._last_settings = self._next_settings
            else:
                packet = self._last_settings.to_packet(changed=False)

            self._serial.write(packet)
            result = self._serial.read(12)
            assert len(result) == 12
            await aioconsole.aprint(repr(result))

    async def user_loop(self):
        while True:
            try:
                cmd = await aioconsole.ainput()
                attribute, value = cmd.split('=', 1)
                if attribute in {"resistor_heating", "running", "plasma", "swivel", "swirl"}:
                    value = value.lower() in {"y", "yes", "on", "true"}
                elif attribute in {"room_temperature", "set_temperature"}:
                    value = float(value)
                elif attribute == "mode":
                    value = structs.Mode[value.upper()]
                elif attribute == "fan_speed":
                    value = structs.FanSpeed[value.upper()]
                else:
                    await aioconsole.aprint(f"I don't know {cmd}")
                    continue
            
                self._next_settings = dataclasses.replace(self._last_settings, **{attribute: value})
            except Exception as error:
                await aioconsole.aprint(f"ooops: {error}")

    def run(self, loop: asyncio.AbstractEventLoop):
        loop.create_task(self.bus_loop())
        loop.run_until_complete(self.user_loop())


@click.command()
@click.option("--period-sec", type=click.IntRange(min=2), default=4)
@click.argument(
    "serial-port", type=click.Path(dir_okay=False, file_okay=True, writable=True)
)
def main(period_sec: int, serial_port: str) -> None:
    loop = asyncio.get_event_loop()

    emu = PanelEmu(serial_port, datetime.timedelta(seconds=period_sec))
    emu.run(loop)


if __name__ == "__main__":
    main()
