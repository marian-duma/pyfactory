from lib.ArmRobot import UniversalRobot
import time
class FeedRobot(UniversalRobot):
    def __init__(self, robot_name='UR3', init_position=None) -> None:
        super().__init__(robot_name)
        
        if init_position == None:
            self.init_position = self.ReadPosition()
        else:
            self.init_position = init_position
        self.speed = 50
        self.height_offset = 0.1
        
    
    def pick_cube(self, cube, target):
        self.sim.setObjectInt32Param(cube, self.sim.shapeintparam_static, 1)
        self.sim.setObjectInt32Param(cube, self.sim.shapeintparam_respondable, 0)
        self.MoveL(target, self.speed)
        self.MoveL([*target[0:2], target[2] - self.height_offset * 200, *target[3:6]], self.speed + 50)
        self.sim.setObjectParent(cube, self.simTip, True)
        self.MoveL([*target[0:2], target[2] + self.height_offset * 200, *target[3:6]], self.speed + 50)
        
        
    def release_cube(self, cube, target):
        self.MoveL(target, self.speed)
        self.sim.setObjectParent(cube, -1, True)
        self.sim.setObjectInt32Param(cube, self.sim.shapeintparam_static, 0)
        self.sim.setObjectInt32Param(cube, self.sim.shapeintparam_respondable, 1)

    def reset(self):
        self.SetPosition(self.init_position)