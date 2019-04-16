""" I don't have enough deletions to fix this, so I'll comment it out.
TODO: type annotate each instance variable, either use Vector3.modified method in `update` instead of `.data` or just create a new Vector3 object (which is slower)

from vectors import Vector3
class CarObject:
    def __init__(self, index, car=None):
        self.location = Lector3(0,0,0)
        self.velocity = Lector3(0,0,0)
        #self.matrix = Matrix3([0,0,0])
        #self.rvel = Vector3(0,0,0)
        self.team = 0
        self.boost= 0
        self.airborn = False
        self.index = index
        if car != None:
            self.update(car)
        self.modified = False
    def update(self,packet):
        self.location.data = [packet.physics.location.x,packet.physics.location.y,packet.physics.location.z]
        self.velocity.data = [packet.physics.velocity.x,packet.physics.velocity.y,packet.physics.velocity.z]
        #self.matrix = Matrix3( [packet.physics.rotation.pitch,packet.physics.rotation.yaw,packet.physics.rotation.roll])
        #self.rvel.data = self.matrix.dot([packet.physics.angular_velocity.x,packet.physics.angular_velocity.y,packet.physics.angular_velocity.z])
        self.team = packet.team
        self.boost = packet.boost
        self.airborn = not packet.has_wheel_contact
        self.modified = True

class BallObject:
    def __init__(self):
        self.location = Vector3(0,0,0)
        self.velocity = Vector3(0,0,0)
    def update(self,packet):
        self.location.data = [packet.physics.location.x,packet.physics.location.y,packet.physics.location.z]
        self.velocity.data = [packet.physics.velocity.x,packet.physics.velocity.y,packet.physics.velocity.z]
"""
