"""
Most of my utils for a robloxbot123 style aerial, works best when car is slow/stationary (or moving towards rough intercept of ball)
Fair warning, some of the function names have been renamed, and some of this code is from different and incompatible gosling versions
It'll need work work but I'll be around to answer any questions - GooseFairy
"""

import math

from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.ball_prediction_struct import BallPrediction, Slice

from .vectors import *
from .utils import sign, clamp
from .matrix import Matrix3D

# Holds relevant information from the packet
class Info:
    def __init__(self, packet: GameTickPacket, index):
        self.game_time = packet.game_info.seconds_elapsed
        self.car = packet.game_cars[index]
        self.car_location = Vector3(
            self.car.physics.location.x, self.car.physics.location.y, self.car.physics.location.z
        )
        self.car_velocity = Vector3(
            self.car.physics.velocity.x, self.car.physics.velocity.y, self.car.physics.velocity.z
        )
        self.car_matrix = Matrix3D(
            [self.car.physics.rotation.pitch, self.car.physics.rotation.yaw, self.car.physics.rotation.roll]
        )
        self.rotation_velocity = self.car_matrix.dot(self.car.physics.angular_velocity)
        self.ball = packet.game_ball
        self.ball_location = Vector3(
            self.ball.physics.location.x, self.ball.physics.location.y, self.ball.physics.location.z
        )
        self.ball_velocity = Vector3(
            self.ball.physics.velocity.x, self.ball.physics.velocity.y, self.ball.physics.velocity.z
        )


def default_pd(
    info: Info, local: Vector3, error: bool = False
):  # Generates controller outputs to get the car facing a given local coordinate while airborne.
    e1 = math.atan2(
        local.y, local.x
    )  # Input is the agent (specifically its rotataional velocity converted to local coordinates), the local coordinates of the target, and a bool to return the yaw angle if you want
    steer = steer_pd(
        e1, 0
    )  # local coordinate is in forward,left,up format. rvel is the rotational velocity of the forward axis
    yaw = steer_pd(e1, -info.rotation_velocity.z / 6)
    e2 = math.atan2(local.z, local.x)
    pitch = steer_pd(e2, info.rotation_velocity.y / 6)
    roll = steer_pd(-info.car.physics.rotation.roll, info.rotation_velocity.x / 6)  # keeps the bot upright
    if error == False:
        return steer, yaw, pitch, roll
    else:
        return steer, yaw, pitch, roll, abs(e1) + abs(e2)


def dpp3D(
    target_loc: Vector3, target_vel: Vector3, our_loc: Vector3, our_vel: Vector3
) -> float:  # finds the closing speed between two objects, aka second derivative of distance. could probably be done with vector math too.
    d = (target_loc - our_loc).length
    if d != 0:
        return (
            ((target_loc.x - our_loc.x) * (target_vel.x - our_vel.x))
            + ((target_loc.y - our_loc.y) * (target_vel.y - our_vel.y))
            + ((target_loc.z - our_loc.z) * (target_vel.z - our_vel.z))
        ) / d
    else:
        return 0


def future(
    location: Vector3, velocity: Vector3, time: float, path: BallPrediction = None
) -> Vector3:  # calculates future position of object assuming it follows a projectile trajectory
    if path is None:
        x = location.x + (velocity.x * time)
        y = location.y + (velocity.y * time)
        z = location.z + (velocity.z * time) - (325 * time * time)
        return Vector3(x, y, z)
    else:
        s: Slice = path.slices[int(time * 60)]
        return Vector3(s.physics.location.x, s.physics.location.y, s.physics.location.z)


def backsolve_future(
    location: Vector3, velocity: Vector3, future: Vector3, time: float, radius: float = 92.75
) -> Vector3:  # finds acceleration needed to arrive at a future given a location and time
    d = future - location
    d -= d.normalized * radius
    dx = (2 * ((d.x / time) - velocity.x)) / time
    dy = (2 * ((d.y / time) - velocity.y)) / time
    dz = (2 * ((325 * time) + ((d.z / time) - velocity.z))) / time
    return Vector3(dx, dy, dz)


def steer_pd(angle, rate):  # little steering util
    final = ((35 * (angle + rate)) ** 3) / 20
    return clamp(final, -1, 1)  # clamp


class aerial_option_b:  # call at your own risk: yeets towards ball after taking a mostly wild guess at where it will be.
    def __init__(self, game_time_started: float):
        self.time = -9
        self.jt = game_time_started
        self.target: Vector3 = None

    def execute(self, packet: GameTickPacket, index, ball_prediction: BallPrediction = None) -> SimpleControllerState:
        info = Info(packet, index)

        if self.time == -9:  # if we don't have a target time, guess one using really bad math
            eta = math.sqrt(((info.ball_location - info.car_location).length) / 529.165)
            targetetaloc = future(info.ball_location, info.ball_velocity, eta)
            before = abs(dpp3D(info.ball_location, info.ball_velocity, info.car_location, info.car_velocity))
            after = abs(dpp3D(targetetaloc, info.ball_velocity, info.car_location, info.car_velocity))
            if sign(before) == sign(after):  # sign returns 1 or -1
                eta = math.sqrt(clamp(((info.ball_location - info.car_location).length + before) / 529.165, 0.01, 9999))
            else:
                eta = math.sqrt(
                    clamp(((info.ball_location - info.car_location).length + before + after) / 529.165, 0.01, 9999)
                )
            test = dpp3D(targetetaloc, info.ball_velocity, info.car_location, info.car_velocity)
            eta = math.sqrt(((info.ball_location - info.car_location).length + max(0, test)) / 529.165)
            self.time = info.game_time + eta
            target = Vector3(0, 0, 0)
        else:
            time_remain = clamp(
                self.time - info.game_time, -2.0, 10.0
            )  # agent will continue aerial up to 2 seconds after predicted intercept time
            if time_remain != 0:
                target = future(info.ball_location, info.ball_velocity, time_remain, ball_prediction)
            else:
                time_remain = 0.1
                target = future(info.ball_location, info.ball_velocity, 0.1, ball_prediction)

            # Shooting offset
            enemy_goal = Vector3(0, (1 if info.car.team == 0 else -1) * 5120, clamp(target.z / 2, 100, 600))
            target += (target - enemy_goal).normalized * 100

            """
            if time_remain > -1.9:
                target = backsolve_future(info.car_location, info.car_velocity, target, time_remain, radius = 0)
            else:
                target = info.car_velocity
            """
            target = backsolve_future(info.car_location, info.car_velocity, target, time_remain, radius=0)
        controller, self.jt = deltaC(info, target, self.jt)
        self.target = target
        return controller


def deltaC(
    info: Info, target: Vector3, jt
):  # this controller takes a vector containing the required acceleration to reach a target, and then gets the car there
    c = SimpleControllerState()
    target_local = info.car_matrix.dot(target)
    if info.car.has_wheel_contact:  # if on the ground
        if jt + 1.5 > info.game_time:  # if we haven't jumped in the last 1.5 seconds
            c.jump = True
        else:
            c.jump = False
            jt = info.game_time
    else:
        c.steer, c.yaw, c.pitch, c.roll, error = default_pd(info, target_local, True)
        if target.length > 25:  # stops boosting when "close enough"
            c.boost = True
        if error > 0.9:  # don't boost if we're not facing the right way
            c.boost = False
        tsj = info.game_time - jt  # time since jump
        if tsj < 0.215:
            c.jump = True
        elif tsj < 0.25:
            c.jump = False
        elif tsj >= 0.25 and tsj < 0.27 and target.z > 560:  # considers a double-jump if we still need to go up a lot
            c.jump = True
            c.boost = False
            c.yaw = c.pitch = c.roll = 0
        else:
            c.jump = False
        c.throttle = 1
    return c, jt
