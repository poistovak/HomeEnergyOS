from dataclasses import dataclass

from .objective import Objective


@dataclass

class Priority:

    objective: Objective

    score: float