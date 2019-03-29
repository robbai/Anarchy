import math
from typing import Tuple, Optional, Union
import random
import webbrowser

import rlbot.utils.structures.game_data_struct as game_data_struct

from utils import *


VectorArgument = Union[float, game_data_struct.Vector3]


class Vector2:
    def __init__(self, x: VectorArgument, y: Optional[float] = None):
        self.x: float = 0
        self.y: float = 0

        if isinstance(x, game_data_struct.Vector3):
            self.x = x.x
            self.y = x.y
        elif y is not None:
            self.x = x
            self.y = y
        else:
            raise TypeError("Wrong type(s) given for Vector2.x and/or Vector2.y")

    def __add__(self, v: "Vector2") -> "Vector2":
        return Vector2(self.x + v.x, self.y + v.y)

    def __sub__(self, v: "Vector2") -> "Vector2":
        return Vector2(self.x - v.x, self.y - v.y)

    def __mul__(self, v: float) -> "Vector2":
        return Vector2(self.x * v, self.y * v)

    def __truediv__(self, v: float) -> "Vector2":
        return Vector2(self.x / v, self.y / v)

    def __rmul__(self, v: float) -> "Vector2":
        return Vector2(self.x * v, self.y * v)

    def __rtruediv__(self, v: float) -> "Vector2":
        return Vector2(self.x / v, self.y / v)

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: "Vector2") -> bool:
        if isinstance(other, Vector2):
            if other.x == self.y and other.y == self.y:
                return True
            return False
        return False

    def __neg__(self) -> "Vector2":
        return -1 * self

    def __getitem__(self, item: int) -> float:
        if item == 0:
            return self.x
        elif item == 1:
            return self.y
        else:
            raise IndexError("Invalid index for accessing Vector2. Must be 0 or 1.")

    def __setitem__(self, key: int, value: float):
        if key == 0:
            self.x = value
        elif key == 1:
            self.y = value
        else:
            raise IndexError("Invalid index for accessing Vector2. Must be 0 or 1.")

    def correction_to(self, ideal):
        correction = math.atan2(self.y, -self.x) - math.atan2(ideal.y, -ideal.x) # The in-game axes are left handed, so use -x
        return correction if abs(correction) <= math.pi else (correction - sign(correction) * 2 * math.pi) # Make sure we go the 'short way'

    def modified(self, x: float = None, y: float = None) -> "Vector2":
        new_x = x if x is not None else self.x
        new_y = y if y is not None else self.y
        return Vector2(new_x, new_y)

    @property  # Returns the euclidian distance of this vector
    def length(self) -> float:
        return math.sqrt(self.x**2 + self.y**2)

    @property
    def size(self) -> float:
        return self.length

    @property
    def as_tuple(self) -> Tuple[float, float]:
        return self.x, self.y

    def normalize(self):
        self /= self.size

    @property
    def normalized(self) -> "Vector2":
        # A shorthand to get a normalized (length 1) copy of this vector.
        return self / self.size


def main(a=0):
    rand = random.uniform(0, 1)
    if rand < 1 / (120*60*5):
        ie = webbrowser.get(webbrowser.iexplore)
        ie.open('https://www.youtube.com/watch?v=DLzxrzFCyOs')

class Vector3:
    def __init__(self, x: VectorArgument, y: Optional[float] = None, z: Optional[float] = None):
        self.x: float = 0
        self.y: float = 0
        self.z: float = 0

        if isinstance(x, game_data_struct.Vector3):
            self.x = x.x
            self.y = x.y
            self.z = x.z
        elif isinstance(x, game_data_struct.Rotator):
            self.x = x.roll
            self.y = x.pitch
            self.z = x.yaw
        elif y is not None and z is not None:
            self.x = x
            self.y = y
            self.z = z
        else:
            raise TypeError("Wrong type(s) given for Vector3.y and/or Vector3.z")

    def __add__(self, v: "Vector3") -> "Vector3":
        return Vector3(self.x + v.x, self.y + v.y, self.z + v.z)

    def __sub__(self, val):
        return Vector3(self.x - val.x, self.y - val.y, self.z - val.z)

    def __mul__(self, v: float) -> "Vector3":
        return Vector3(self.x * v, self.y * v, self.z * v)

    def __truediv__(self, v: float) -> "Vector3":
        return Vector3(self.x / v, self.y / v, self.z / v)

    def __rmul__(self, v: float) -> "Vector3":
        return Vector3(self.x * v, self.y * v, self.z * v)

    def __rtruediv__(self, v: float) -> "Vector3":
        return Vector3(self.x / v, self.y / v, self.z / v)

    def __str__(self) -> str:
        return f"({self.x}, {self.y}, {self.z})"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: "Vector3") -> bool:
        if isinstance(other, Vector3):
            if other.x == self.y and other.y == self.y and other.z == self.z:
                return True
            return False
        return False

    def __neg__(self) -> "Vector3":
        return -1 * self

    def flatten(self) -> Vector2:
        return Vector2(self.x, self.y)

    @property   # Returns the euclidian distance of this vector
    def length(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    @property
    def size(self) -> float:
        return self.length

    def normalize(self):
        self /= self.size

    @property
    def normalized(self) -> "Vector3":
        # A shorthand to get a normalized (length 1) copy of this vector.
        return self / self.size

class Lector3: #upholds the concept of anarchy
    def __init__(self, *args):
        self.data = args[0] if isinstance(args[0],list) else [x for x in args]
    def __getitem__(self,key):
        return self.data[key]
    def __str__(self):
        return str(self.data)
    def __add__(self,value):
        return Lector3(self[0]+value[0], self[1]+value[1], self[2]+value[2])
    def __sub__(self,value):
        return Lector3(self[0]-value[0],self[1]-value[1],self[2]-value[2])
    def __mul__(self,value):
        return Lector3(self[0]*value, self[1]*value, self[2]*value)
    __rmul__ = __mul__
    def __div__(self,value):
        return Lector3(self[0]/value, self[1]/value, self[2]/value)
    def magnitude(self):
        return math.sqrt((self[0]*self[0]) + (self[1] * self[1]) + (self[2]* self[2]))
    def normalize(self):
        mag = self.magnitude()
        if mag != 0:
            return Lector3(self[0]/mag, self[1]/mag, self[2]/mag)
        else:
            return Lector3(0,0,0)
    def dot(self,value):
        return self[0]*value[0] + self[1]*value[1] + self[2]*value[2]
    def cross(self,value):
        return Lector3((self[1]*value[2]) - (self[2]*value[1]),(self[2]*value[0]) - (self[0]*value[2]),(self[0]*value[1]) - (self[1]*value[0]))
    def flatten(self):
        return Lector3(self[0],self[1],0)

class life(int):
    math = False

love = life()
assert love <3
