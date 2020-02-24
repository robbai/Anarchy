import math
from rlbot.agents.base_agent import SimpleControllerState, GameTickPacket, BaseAgent
from .action import ActionBase
from utilities.calculations import invert_angle
from utilities.utils import clamp11
from utilities.vectors import Vector3


class Recover(ActionBase):
    def __init__(
        self, agent, roll=True, pitch=True, yaw=True, allow_yaw_wrap: bool = True
    ):
        self.agent = agent
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw
        self.allow_yaw_wrap = allow_yaw_wrap
        self.finished: bool = False

    def step(self, packet: GameTickPacket) -> SimpleControllerState:
        local = self.agent.rotation_matrix.dot(
            self.agent.impact - Vector3(self.agent.car.physics.location)
        )
        steer_correction_radians = math.atan2(local.y, local.x)
        wrap_yaw = (
            self.allow_yaw_wrap
            and abs(steer_correction_radians) > math.pi * 0.75
            and self.pitch
            and self.yaw
        )
        controller: SimpleControllerState = SimpleControllerState()
        if self.roll:
            controller.roll = clamp11(
                self.agent.car.physics.rotation.roll * -3
                + self.agent.rotation_velocity.x * (10 ** 10 if wrap_yaw else 0.3)
            )
        if abs(self.agent.car.physics.rotation.roll) < 1.5 or not self.roll:
            if self.pitch:
                controller.pitch = clamp11(
                    (
                        self.agent.car.physics.rotation.pitch - math.pi
                        if wrap_yaw
                        else self.agent.car.physics.rotation.pitch
                    )
                    * -4
                    + self.agent.rotation_velocity.y * 0.8
                )
            if self.yaw:
                yaw = (
                    invert_angle(steer_correction_radians)
                    if wrap_yaw
                    else steer_correction_radians
                )
                controller.yaw = clamp11(
                    yaw * 3.75 - self.agent.rotation_velocity.z * 0.95
                )
        controller.throttle = 0.03  # Don't turtle.
        controller.jump = False
        if not self.finished:
            self.finished = self.agent.car.has_wheel_contact
        return controller
