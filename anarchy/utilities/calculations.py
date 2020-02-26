import math
from typing import Optional, List, Tuple

from rlbot.utils.structures.ball_prediction_struct import BallPrediction, Slice
from rlbot.utils.structures.game_data_struct import BoostPad, BoostPadState, MAX_BOOSTS

from utilities.utils import sign
from utilities.vectors import Vector3, Vector2

BoostList = BoostPad * MAX_BOOSTS
BoostStateList = BoostPadState * MAX_BOOSTS


def closest_boost(
    player_pos: Vector3, boost_pads: BoostList, boost_pad_states: BoostStateList
) -> Optional[Vector3]:
    """
    :param boost_pads: From self.get_field_info().boost_pads
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
    if angle != 0:
        return -(angle - sign(angle) * math.pi)
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
        acceleration: Vector3 = (
            Vector3(current_slice.physics.velocity)
            - Vector3(prev_slice.physics.velocity)
        ) / (current_slice.game_seconds - prev_slice.game_seconds)
        # The ball's Z acceleration will not be around -650 if it is bouncing.
        if not (-600 > acceleration.z > -680):
            bounces.append(current_slice)

    return bounces


def estimate_max_speed(car, cap_at_sonic: bool = True):
    velocity_vec = Vector2(car.physics.velocity.x, car.physics.velocity.y)
    velocity = velocity_vec.length
    boost = float(car.boost)

    return min(2200.0 if cap_at_sonic else 2300.0, 1410.0 + boost / 33.3 * 991.667)


def throttle_acceleration(speed: float):
    speed = min(2300, abs(speed))
    if speed < 1400:
        return 1600 + speed * -144 / 140
    elif speed < 1410:
        return 160 + (speed - 1400) * -16
    return 0


def get_impact(
    path: BallPrediction, car, start_time: float, renderer=None
) -> Tuple[Vector3, float]:
    wheel_contact = car.has_wheel_contact
    ground_time = (
        bounce_time(
            car.physics.location.z - 17.010000228881836, -car.physics.velocity.z
        )
        if not wheel_contact
        else 0
    )
    car_position = Vector3(car.physics.location)
    car_velocity = Vector3(car.physics.velocity)
    if not wheel_contact:
        car_position += Vector3(car.physics.velocity) * ground_time
        car_position.z = 0
        car_velocity.z = 0
    car_speed = car_velocity.length
    car_distance = 0
    boost = car.boost
    last_time = start_time
    for i in range(0, path.num_slices):
        current_slice: Slice = path.slices[i]
        last_slice: bool = (i == path.num_slices - 1)
        slice_position: Vector3 = Vector3(
            current_slice.physics.location.x,
            current_slice.physics.location.y,
            current_slice.physics.location.z,
        )
        distance = (slice_position - car_position).length - 92.75
        time = current_slice.game_seconds - start_time
        if time >= ground_time or last_slice:
            delta_time = time - last_time
            acceleration = (
                throttle_acceleration(car_speed) + (boost >= 1) * 911 + (2 / 3)
            )
            car_distance += (
                car_speed * delta_time + 0.5 * acceleration * delta_time ** 2
            )
            car_speed += acceleration * delta_time
            boost -= 33.3 * delta_time
            if car_distance > distance or last_slice:
                if renderer is not None:
                    renderer.begin_rendering("Impact")
                    renderer.draw_line_3d(
                        car_position,
                        slice_position,
                        renderer.cyan() if car.team == 0 else renderer.orange(),
                    )
                    renderer.end_rendering()
                return slice_position, time
        last_time = time
    return None, 0  # Couldn't find a point of impact


def distance_from_wall(point: Vector2) -> float:
    return min(4096 - abs(point.x), 5120 - abs(point.y))


def turning_radius(car_speed: float) -> float:  # Thx Dom
    return (
        156
        + 0.1 * car_speed
        + 0.000069 * car_speed ** 2
        + 0.000000164 * car_speed ** 3
        - 5.62e-11 * car_speed ** 4
    )


def inside_turning_radius(local: Vector3, car_speed: float) -> bool:
    turn_radius = turning_radius(car_speed)
    return turn_radius > min(
        (local - Vector3(0, -turn_radius, 0)).length,
        (local - Vector3(0, turn_radius, 0)).length,
    )


def project_to_wall(point: Vector2, direction: Vector2) -> Vector2:
    wall = Vector2(sign(direction.x) * 4096, sign(direction.y) * 5120)
    dir_normal = direction.normalized

    x_difference = (
        abs((wall.x - point.x) / dir_normal.x) if dir_normal.x != 0 else 10000
    )
    y_difference = (
        abs((wall.y - point.y) / dir_normal.y) if dir_normal.y != 0 else 10000
    )

    if x_difference < y_difference:
        # Side wall is closer
        return Vector2(wall.x, point.y + dir_normal.y * x_difference)
    else:
        # Back wall is closer
        return Vector2(point.x + dir_normal.x * y_difference, wall.y)
