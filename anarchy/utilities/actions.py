import math

from utilities.calculations import invert_angle
from utilities.utils import clamp11, sign
from utilities.vectors import Vector3


def recover(
    self,
    rotation_velocity: Vector3,
    roll=True,
    pitch=True,
    yaw=True,
    allow_yaw_wrap: bool = True,
):
    wrap_yaw = (
        allow_yaw_wrap
        and abs(self.steer_correction_radians) > math.pi * 0.75
        and pitch
        and yaw
    )
    if roll:
        self.controller.roll = clamp11(
            self.car.physics.rotation.roll * -3 + rotation_velocity.x * 0.3
        )
    if abs(self.car.physics.rotation.roll) < 1.5 or not roll:
        if pitch:
            self.controller.pitch = clamp11(
                (
                    self.car.physics.rotation.pitch - math.pi
                    if wrap_yaw
                    else self.car.physics.rotation.pitch
                )
                * -4
                + rotation_velocity.y * 0.8
            )
        if yaw:
            self.controller.yaw = clamp11(
                (
                    invert_angle(self.steer_correction_radians)
                    if wrap_yaw
                    else self.steer_correction_radians
                )
                * 3.75
                - rotation_velocity.z * 0.95
            )


def dodge(self, angle: float, rotation_velocity: Vector3, multiply=1):
    self.controller.yaw = 0
    if self.car.has_wheel_contact and not self.dodging:
        self.dodge_angle = angle
        self.dodging = True
        self.controller.jump = True
        self.controller.pitch = -sign(math.cos(self.dodge_angle))
        self.next_dodge_time = self.time + 0.25

    else:
        if self.time > self.next_dodge_time:
            self.controller.jump = True
            if self.car.has_wheel_contact or self.time > self.next_dodge_time + 1.5:
                self.dodging = False
        if self.time < self.next_dodge_time + 0.5:
            self.controller.roll = clamp11(math.sin(self.dodge_angle) * multiply)
            self.controller.pitch = clamp11(-math.cos(self.dodge_angle))
        elif self.time < self.next_dodge_time + 1:
            self.controller.roll = 0
            self.controller.pitch = 0
        else:
            recover(self, rotation_velocity, yaw=(self.car.physics.location.z > 1000))


def halfflip(self, rotation_velocity: Vector3):
    self.controller.roll = 0
    self.controller.pitch = 0
    self.controller.yaw = 0
    if not self.halfflipping and self.car.has_wheel_contact:
        self.halfflipping = True
        self.controller.jump = True
        self.next_dodge_time = self.time
    elif self.time > self.next_dodge_time + 1.0:
        self.halfflipping = False
    elif self.time > self.next_dodge_time + 0.6:
        self.controller.pitch = -1
        self.controller.roll = 1
        if self.time > self.next_dodge_time + 0.9:
            recover(self, rotation_velocity, yaw=(self.car.physics.location.z > 1000))
        if self.car.has_wheel_contact:
            self.halfflipping = False
    elif self.time > self.next_dodge_time + 0.3:
        self.controller.jump = (
            self.time % 0.1
        ) < 0.05  # Spam the jump button to ensure the flip
        self.controller.pitch = 1
