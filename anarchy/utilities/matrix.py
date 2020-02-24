import math

from .vectors import Vector3


class Matrix3D:
    def __init__(self, r):
        CR = math.cos(r[2])
        SR = math.sin(r[2])
        CP = math.cos(r[0])
        SP = math.sin(r[0])
        CY = math.cos(r[1])
        SY = math.sin(r[1])
        self.data = [
            Vector3(CP * CY, CP * SY, SP),
            Vector3(CY * SP * SR - CR * SY, SY * SP * SR + CR * CY, -CP * SR),
            Vector3(-CR * CY * SP - SR * SY, -CR * SY * SP + SR * CY, CP * CR),
        ]

    def dot(self, vector):
        return Vector3(
            self.data[0].dot(vector), self.data[1].dot(vector), self.data[2].dot(vector)
        )

    def __getitem__(self, item: int):
        return self.data[item]

    def __setitem__(self, key: int, value: Vector3):
        self.data[key] = value
