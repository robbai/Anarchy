'''Most of my utils for a robloxbot123 style aerial, works best when car is slow/stationary (or moving towards rough intercept of ball)
Fair warning, some of the function names have been renamed, and some of this code is from different and incompatible gosling versions
It'll need work work but I'll be around to answer any questions - GooseFairy

def default_pd(agent, local, error = False):    #Generates controller outputs to get the car facing a given local coordinate while airborne. 
    e1 = math.atan2(local[1],local[0])            #Input is the agent (specifically its rotataional velocity converted to local coordinates), the local coordinates of the target, and a bool to return the yaw angle if you want
    steer = steerPD(e1,0)                                 #local coordinate is in forward,left,up format. rvel is the rotational velocity of the forward axis
    yaw = steerPD(e1,-agent.me.rvel[2]/5)
    e2 = math.atan2(local[2],local[0])
    pitch = steerPD(e2,agent.me.rvel[1]/5)
    roll = 0   #steerPD(math.atan2(agent.me.matrix.data[2][1],agent.me.matrix.data[2][2]),agent.me.rvel[0]/5)#keeps the bot upright, uses ep6 rotation matricies tho
    if error == False:
        return steer,yaw,pitch,roll
    else:
        return steer,yaw,pitch,roll,abs(e1)+abs(e2)
    
def dpp3D(target_loc,target_vel,our_loc,our_vel): #finds the closing speed between two objects, aka second derivative of distance. could probably be done with vector math too.
    d = distance3D(target_loc,our_loc)
    if d!=0:
        return (((target_loc[0] - our_loc[0]) * (target_vel[0] - our_vel[0])) + ((target_loc[1] - our_loc[1]) * (target_vel[1] - our_vel[1])) + ((target_loc[2] - our_loc[2]) * (target_vel[2] - our_vel[2])))/d
    else:
        return 0
    
def future(obj,time): #calculates future position of object assuming it follows a projectile trajectory
    x = obj.location[0] + (obj.velocity[0] * time)
    y = obj.location[1] + (obj.velocity[1] * time)
    z = obj.location[2] + (obj.velocity[2] * time) - (325 * time * time)
    return Vector3(x,y,z)

def backsolveFuture(location,velocity,future,time): #finds acceleration needed to arrive at a future given a location and time
    d = future-location
    dx = (2* ((d[0]/time)-velocity[0]))/time
    dy = (2* ((d[1]/time)-velocity[1]))/time
    dz = (2 * ((325*time)+((d[2]/time)-velocity[2])))/time
    return Vector3(dx,dy,dz)

def steer_pd(angle,rate):   #little steering util
    final = ((35*(angle+rate))**3)/20
    return cap(final,-1,1) #clamp

class aerial_option_b:#call at your own risk: yeets towards ball after taking a mostly wild guess at where it will be. 
    def __init__(self):
        self.time = -9
        
    def execute(self,agent):
        if self.time == -9: #if we don't have a target time, guess one using really bad math
            eta = math.sqrt(((agent.ball.location - agent.me.location).magnitude())/529.165)
            targetetaloc = future(agent.ball, eta)
            before = dpp3D(agent.ball.location,agent.ball.velocity,agent.me.location,agent.me.velocity)
            after = dpp3D(targetetaloc,agent.ball.velocity,agent.me.location,agent.me.velocity)
            if sign(before) == sign(after): #sign returns 1 or -1
                eta = math.sqrt(((agent.ball.location - agent.me.location).magnitude()+before)/529.165)
            else:
                eta = math.sqrt(((agent.ball.location - agent.me.location).magnitude()+before+after)/529.165)
            test = dpp3D(targetetaloc,agent.ball.velocity,agent.me.location,agent.me.velocity)
            eta = math.sqrt(((agent.ball.location - agent.me.location).magnitude()+test)/529.165)
            self.time = agent.game_time + eta
            target = Vector3(0,0,0)
        else:
            time_remain = cap(self.time - agent.game_time, -2.0,10.0) #agent will continue aerial up to 2 seconds after predicted intercept time
            if time_remain != 0:
                target = future(agent.ball, time_remain)
            else:
                time_remain = 0.1
                target = future(agent.ball, 0.1)
            if time_remain > -1.9:
                target = backsolveFuture(agent.me.location,agent.me.velocity, target,time_remain)
            else:
                target = agent.me.velocity
        return deltaC(agent,target)
    
def deltaC(agent, target): #this controller takes a vector containing the required acceleration to reach a target, and then gets the car there
    c = SimpleControllerState()
    target_local = toLocal(agent.me.location + target, agent.me) #old gosling "global -> local" function, todo is replace with something not bad
    if agent.me.grounded: #if on the ground
        if agent.jt + 1.5 > agent.game_time: #if we haven't jumped in the last 1.5 seconds
            c.jump = True
        else:
            c.jump = False
            agent.jt = agent.game_time
    else:
        c.steer,c.yaw,c.pitch,c.roll,error = default_pd(agent, target_local, True)
        if target.magnitude() > 25: #stops boosting when "close enough"
            c.boost = True
        if error > 0.9: #don't boost if we're not facing the right way
            c.boost = False
        tsj = agent.game_time - agent.jt #time since jump
        if tsj < 0.215:
            c.jump = True
        elif tsj < 0.25:
            c.jump = False
        elif tsj >=0.25 and tsj < 0.27 and target.data[2]>560: #considers a double-jump if we still need to go up a lot
            c.jump = True
            c.boost = False
            c.yaw = c.pitch = c.roll = 0
        else:
            c.jump = False            
    return c
'''
