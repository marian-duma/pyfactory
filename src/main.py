import sys
import signal
import time

from lib.ArmRobot import UniversalRobot
from lib.interpolation import linear_interpolation

import utils.connection as connection
from utils.environment import create_boxes


from handlers.cube_generator import CubeGenerator
from handlers.conveyor_handler import ConveyorHandler
from handlers.feed_robot import FeedRobot
from handlers.tetromino_generator import TetrominoGenerator
from handlers.vision import ShapeDetector

from managers.feed_manager import FeedManager


# Global state of the program
is_running = True

# SIGINT handler (CTRL+C)
def signal_handler(sig, frame):
    global is_running
    print("\nCTRL+C detected! Program is closing...")
    is_running = False



def main():
    global is_running
    signal.signal(signal.SIGINT, signal_handler)

    # TODO: load the scene at runtime
    client,sim = connection.connect_to_sim()

    # Configuration variables
    # TODO: implement proper classes or config files
    MOTOR_SPEED = 1.0

    sim.stopSimulation()
    time.sleep(0.5)
    sim.startSimulation()
    
    generator = TetrominoGenerator(sim)
    conveyor = ConveyorHandler(sim, "/conveyor")
    robot = FeedRobot('UR5')
    
    feed_manager = FeedManager(generator, conveyor, robot, "/pick_cube_target", "/release_cube_target")

    print("Simulation started. Press CTRL+C to stop.")
    start_time = sim.getSimulationTime()
    base_pos: list[int] = sim.getObjectPosition(robot.simRobot, -1)
    boxes = create_boxes(sim, base_pos)
    shape_detector = ShapeDetector(sim)
    color_map = {
        "YELLOW": 0,
        "RED": 1,
        "ORANGE": 2,  # Grouping warm colors together
        "GREEN": 3,
        "UNKNOWN": 0  # Dump unidentified objects into the first box
    }
    
    box_index = 0
    try:
        while is_running:
            # AI / control logic:
            feed_manager.start_band()
            feed_manager.next_shape()
            feed_manager.move_away_handle()
            while not feed_manager.conveyor.should_stop():
                pass
            
            feed_manager.stop_band()
            time.sleep(0.5)
            color = shape_detector.get_color2()
            # shape, pos = shape_detector.get_shape_and_world_pos()
            feed_manager.pick_cube()
            
            
            current_joints = robot.ReadJointPosition()
    
            # Force ONLY the base joint (joint 1) to swing over toward the box.
            # Leave the other 5 joints exactly where they are right now.
            escape_joints = [90.0, *current_joints[1:6]]
            
            # Use your class's joint movement function to smoothly pivot the waist
            robot.MoveJ(escape_joints, speed=30)
            
            target_box_index = color_map.get(color, 0)
            target_box = boxes[target_box_index]
            box_pos = feed_manager.robot.GetObjectPosition2(target_box)
            sim.setObjectPosition(feed_manager.release_handle, feed_manager.robot.simRobot, [box_pos[0]/1000, box_pos[1]/1000 + 0.175, box_pos[2]/1000 + 0.2])
            feed_manager.release_cube()
            
            robot.MoveJ([-escape_joints[0], *escape_joints[1:]], speed=30) 
            
            box_index += 1
            client.step()

    except Exception as e:
        print(f"\nAn error occurred during execution: {e}")

    finally:
        try:
            robot.SetPosition(robot.init_position)
            sim.stopSimulation()
            print("Simulation stopped!")
        except Exception as e:
            print(f"Failed to stop simulation cleanly. ZMQ Socket state broken. {e}")
        sys.exit(0)

if __name__ == "__main__":
    main()