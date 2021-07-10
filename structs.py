# SPDX-FileCopyrightText: 2021 Diego Elio Pettenò
#
# SPDX-License-Identifier: 0BSD

import dataclasses
import enum
from typing import List

import construct
from construct.core import Byte, Check, Checksum


@enum.unique
class Mode(enum.IntEnum):
    COOL = 0x0
    DH = 0x1
    FAN = 0x2
    AUTO = 0x3
    HEAT = 0x4


@enum.unique
class FanSpeed(enum.IntEnum):
    LOW = 0x0
    MEDIUM = 0x1
    HIGH = 0x2
    POWER = 0x4


def calculate_checksum(b: List[int]) -> int:
    assert len(b) == 5

    return (sum(b) & 0xFF) ^ 0x55


HVAC_CONTROL = construct.Struct(
    data=construct.RawCopy(
        construct.BitStruct(
            config=construct.Flag,
            mode=construct.Mapping(
                construct.BitsInteger(3), {e: e.value for e in Mode}
            ),
            resistor_heating=construct.Flag,
            running=construct.Flag,
            unknown1=construct.Flag,
            changed=construct.Flag,
            raw_room_temperature=construct.BitsInteger(8),
            actual_room_temperature=construct.Computed(
                (construct.this.raw_room_temperature / 2) + 10
            ),
            plasma=construct.Flag,
            fan_speed=construct.Mapping(
                construct.BitsInteger(3), {e: e.value for e in FanSpeed}
            ),
            raw_set_temperature=construct.Nibble,
            actual_set_temperature=construct.Computed(
                construct.this.raw_set_temperature + 16
            ),
            unknown3=construct.BitsInteger(2),
            swivel=construct.Flag,
            unknown4=construct.BitsInteger(5),
            unknown5=construct.BitsInteger(7),
            swirl=construct.Flag,
        )
    ),
    checksum=construct.Checksum(
        construct.Byte, calculate_checksum, construct.this.data.data
    ),
)


@dataclasses.dataclass(eq=True)
class Settings:
    mode: Mode = Mode.COOL
    resistor_heating: bool = False
    running: bool = False
    room_temperature: int = 26.5
    plasma: bool = False
    fan_speed: FanSpeed = FanSpeed.HIGH
    set_temperature: int = 18
    swivel: bool = False
    swirl: bool = False

    def to_packet(self, changed: bool = False) -> bytes:
        return HVAC_CONTROL.build(
            {
                "data": {
                    "value": dict(
                        config=False,
                        mode=self.mode,
                        resistor_heating=self.resistor_heating,
                        running=self.running,
                        unknown1=False,
                        changed=changed,
                        raw_room_temperature=int((self.room_temperature - 10) * 2),
                        plasma=self.plasma,
                        fan_speed=self.fan_speed,
                        raw_set_temperature=int(self.set_temperature - 16),
                        unknown3=0,
                        swivel=self.swivel,
                        unknown4=0,
                        unknown5=0,
                        swirl=self.swirl,
                    )
                }
            }
        )
