from enum import Enum


class Strategy(Enum):

    ECONOMY = "economy"

    SELF_CONSUMPTION = "self_consumption"

    BACKUP = "backup"

    EV_PRIORITY = "ev_priority"

    PERFORMANCE = "performance"