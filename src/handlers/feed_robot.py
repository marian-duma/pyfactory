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
        self.height_offset = 0.09
        self.suction_script = self.sim.getScript(self.sim.scripttype_childscript, f"/{robot_name}/suctionPad")
        
    
    def pick_cube(self, cube, target):
        self.MoveL(target, self.speed)
        self.MoveL([*target[0:2], target[2] - self.height_offset * 200, *target[3:6]], self.speed + 50)
        self.sim.callScriptFunction("setSuction", self.suction_script, {"state": True})
        self.sim.setObjectParent(cube, self.simTip, True)
        self.MoveL([*target[0:2], target[2] + self.height_offset * 200, *target[3:6]], self.speed + 50)
        
        
    def release_cube(self, cube, target):
        self.MoveL(target, self.speed)
        self.sim.callScriptFunction("setSuction", self.suction_script, {"state": False})
        self.sim.setObjectParent(cube, -1, True)

    def reset(self):
        self.SetPosition(self.init_position)