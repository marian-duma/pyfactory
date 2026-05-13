import sys
import signal
import time

from lib.ArmRobot import UniversalRobot
from lib.interpolation import linear_interpolation

import utils.connection as connection

from handlers.cube_generator import CubeGenerator
from handlers.conveyor_handler import ConveyorHandler
from handlers.feed_robot import FeedRobot

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
    
    generator = CubeGenerator(sim)
    conveyor = ConveyorHandler(sim, "/conveyor")
    robot = FeedRobot('UR3')
    
    feed_manager = FeedManager(generator, conveyor, robot, "/pick_cube_target", "/release_cube_target")

    print("Simulation started. Press CTRL+C to stop.")
    start_time = sim.getSimulationTime()
    
    try:
        while is_running:
            # AI / control logic:
            feed_manager.start_band()
            feed_manager.next_cube()
            time.sleep(2)
            feed_manager.stop_band()
            time.sleep(0.5)
            feed_manager.pick_cube()
            feed_manager.release_cube()
            # client.step()

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