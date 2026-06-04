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

    client,sim = connection.connect_to_sim()

    sim.stopSimulation()
    time.sleep(0.5)
    sim.startSimulation()
    
    generator = TetrominoGenerator(sim)
    conveyor = ConveyorHandler(sim, "/conveyor")
    robot = FeedRobot('UR5')
    shape_detector = ShapeDetector(sim)
    feed_manager = FeedManager(generator, conveyor, robot, shape_detector, "/pick_cube_target", "/release_cube_target")

    print("Simulation started. Press CTRL+C to stop.")
    base_pos: list[int] = sim.getObjectPosition(robot.simRobot, -1)
    boxes = create_boxes(sim, base_pos)
    
    color_map = {
        "YELLOW": 0,
        "RED": 1,
        "ORANGE": 2,
        "GREEN": 3,
        "UNKNOWN": 0  # Dump unidentified objects into the first box
    }
    
    try:
        while is_running:
            # AI / control logic:
            feed_manager.start_band()
            if not feed_manager.conveyor.should_stop():
                feed_manager.next_shape()
            feed_manager.move_away_handle()
            while not feed_manager.conveyor.should_stop():
                pass
            
            feed_manager.stop_band()
            time.sleep(0.5)
            color = feed_manager.get_color()
            feed_manager.pick_cube()
            feed_manager.release_cube(color, color_map, boxes)
            
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