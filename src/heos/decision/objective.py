from enum import Enum


class Objective(Enum):

    CHARGE_BATTERY = "charge_battery"

    CHARGE_EV = "charge_ev"

    HEAT_WATER = "heat_water"

    EXPORT_POWER = "export_power"

    REDUCE_LOAD = "reduce_load"