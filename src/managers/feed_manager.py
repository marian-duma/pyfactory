import time

from handlers.conveyor_handler import ConveyorHandler
from handlers.cube_generator import CubeGenerator
from handlers.feed_robot import FeedRobot
from handlers.tetromino_generator import TetrominoGenerator
class FeedManager:
    def __init__(self, generator : TetrominoGenerator, conveyor_handler : ConveyorHandler,
                 robot: FeedRobot, pick_cube_target: str, release_cube_target: str) -> None:
        self.sim = robot.sim
        
        self.generator = generator
        self.conveyor = conveyor_handler
        self.robot = robot

        self.picked = None
        self.pick_cube_target = pick_cube_target
        self.release_cube_target = release_cube_target

        self.pick_handle = self.sim.getObject(self.pick_cube_target)
        self.release_handle = self.sim.getObject(self.release_cube_target)
    
    def update(self):
        pass

    def start_band(self):
        self.conveyor.start()
    
    def stop_band(self):
        self.conveyor.stop()
    
    def next_cube(self):
        self.generator.spawn_cube()
        last_cube = self.generator.cubes[-1]
        cube_position = [ x/1000 for x in self.robot.GetObjectPosition2(last_cube)[0:3] ]
        cube_position[2] += self.robot.height_offset
        self.sim.setObjectPosition(self.pick_handle, self.robot.simRobot, self.conveyor.get_cube_position())
        self.sim.setObjectParent(self.pick_handle, last_cube, True)
    
    def next_shape(self):
        shape = self.generator.spawn_random_tetromino()
        self.generator.cubes.append(shape)
        # cube_position = [ x/1000 for x in self.robot.GetObjectPosition2(shape)[0:3] ]
        # while self.conveyor.get_cube_position() is None:
        #     time.sleep(0.1)
        
    
    def pick_cube(self):
        shape = self.generator.cubes[-1]
        cube_position = self.conveyor.get_cube_position()
        cube_position[1] -= 0.03 # type: ignore
        cube_position[2] += self.robot.height_offset # type: ignore
        self.sim.setObjectPosition(self.pick_handle, -1, cube_position)
        self.sim.setObjectParent(self.pick_handle, shape, True)

        self.sim.setObjectParent(self.pick_handle, -1, True)
        self.picked = self.generator.cubes[-1]
        self.robot.pick_cube(self.picked, self.robot.GetObjectPosition2(self.pick_handle))
        
    def release_cube(self):
        self.robot.release_cube(self.picked, self.robot.GetObjectPosition2(self.release_handle))
        self.picked = None
