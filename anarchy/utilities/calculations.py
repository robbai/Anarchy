import math
from typing import Optional
from rlbot.utils.structures.game_data_struct import BoostPad, BoostPadState, MAX_BOOSTS

from utilities.utils import sign
from utilities.vectors import Vector3

BoostList = BoostPad * MAX_BOOSTS
BoostStateList = BoostPadState * MAX_BOOSTS


def closest_boost(player_pos: Vector3, boost_pads: BoostList, boost_pad_states: BoostStateList) -> Optional[Vector3]:
    """
    :param boost_pads: From self.agent.get_field_info().boost_pads
    :param boost_pad_states: From packet.game_boosts
    """
    closest: Optional[Vector3] = None
    closest_dist: float = float("inf")

    for i in range(len(boost_pads)):
        if boost_pads[i].is_full_boost and boost_pad_states[i].is_active:
            pad: Vector3 = Vector3(boost_pads[i].location)
            current_dist: float = (player_pos - pad).length
            if current_dist < closest_dist:
                closest_dist = current_dist
                closest = pad

    return closest


def invert_angle(angle: float) -> float:
    if angle != 0: return -(angle - sign(angle) * math.pi)
    return math.pi
