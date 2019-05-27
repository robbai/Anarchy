import math
from typing import Optional, List

from rlbot.utils.structures.ball_prediction_struct import BallPrediction, Slice
from rlbot.utils.structures.game_data_struct import BoostPad, BoostPadState, MAX_BOOSTS

from utilities.utils import sign
from utilities.vectors import Vector3, Vector2

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


def get_car_facing_vector(car):
    pitch = float(car.physics.rotation.pitch)
    yaw = float(car.physics.rotation.yaw)

    facing_x = math.cos(pitch) * math.cos(yaw)
    facing_y = math.cos(pitch) * math.sin(yaw)

    return Vector2(facing_x, facing_y)


def bounce_time(s: float, u: float, a: float = 650):
    try:
        return (math.sqrt(2 * a * s + u ** 2) - u) / a
    except ZeroDivisionError:
        return 0


def get_ball_bounces(path: BallPrediction) -> List[Slice]:
    """
    Calculates when the ball bounces.

    :param path: The BallPrediction object given by the framework
    :return: BallPrediction Slices when the ball bounces
    """
    bounces: List[Slice] = []

    # Skip the first 10 frames because they cause issues with finding bounces
    for i in range(10, path.num_slices):
        prev_slice: Slice = path.slices[i - 1]
        current_slice: Slice = path.slices[i]
        acceleration: Vector3 = (Vector3(current_slice.physics.velocity) - Vector3(prev_slice.physics.velocity)) / \
                                (current_slice.game_seconds - prev_slice.game_seconds)
        # The ball's Z acceleration will not be around -650 if it is bouncing.
        if not (-600 > acceleration.z > -680):
            bounces.append(current_slice)

    return bounces