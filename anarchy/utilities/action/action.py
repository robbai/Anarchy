from rlbot.agents.base_agent import SimpleControllerState, GameTickPacket
from abc import ABC, abstractmethod


class ActionBase(ABC):
    @abstractmethod
    def step(self, packet: GameTickPacket) -> SimpleControllerState:
        pass
