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
from handlers.tetromino_generator import TetrominoGenerator

# Global state of the program
is_running = True

# SIGINT handler (CTRL+C)
def signal_handler(sig, frame):
    global is_running
    print("\nCTRL+C detected! Program is closing...")
    is_running = False

def create_sorting_box(sim, position, size=[0.3, 0.3, 0.15], wall_thickness=0.01, color=[0.3, 0.3, 0.3]):
    """
    Creates an open-top collection box out of 5 primitive plates.
    
    :param sim: The CoppeliaSim API instance
    :param position: [X, Y, Z] center position for the box base
    :param size: [Width, Length, Height] outer dimensions of the box
    :param wall_thickness: Thickness of the box walls
    :param color: [R, G, B] color array
    """
    bx, by, bz = size
    t = wall_thickness
    
    parts = []
    
    # 1. Base Plate
    base = sim.createPrimitiveShape(sim.primitiveshape_cuboid, [bx, by, t], 0)
    sim.setObjectPosition(base, -1, [position[0], position[1], position[2] + t/2])
    parts.append(base)
    
    # 2. Left Wall (-X side)
    w_left = sim.createPrimitiveShape(sim.primitiveshape_cuboid, [t, by, bz], 0)
    sim.setObjectPosition(w_left, -1, [position[0] - bx/2 + t/2, position[1], position[2] + bz/2])
    parts.append(w_left)
    
    # 3. Right Wall (+X side)
    w_right = sim.createPrimitiveShape(sim.primitiveshape_cuboid, [t, by, bz], 0)
    sim.setObjectPosition(w_right, -1, [position[0] + bx/2 - t/2, position[1], position[2] + bz/2])
    parts.append(w_right)
    
    # 4. Front Wall (+Y side) - adjusts width slightly to fit between side walls
    w_front = sim.createPrimitiveShape(sim.primitiveshape_cuboid, [bx - 2*t, t, bz], 0)
    sim.setObjectPosition(w_front, -1, [position[0], position[1] + by/2 - t/2, position[2] + bz/2])
    parts.append(w_front)
    
    # 5. Back Wall (-Y side)
    w_back = sim.createPrimitiveShape(sim.primitiveshape_cuboid, [bx - 2*t, t, bz], 0)
    sim.setObjectPosition(w_back, -1, [position[0], position[1] - by/2 + t/2, position[2] + bz/2])
    parts.append(w_back)
    
    # Group all 5 plates into a single hollow structure
    box_handle = sim.groupShapes(parts)
    
    # Set visual and physical parameters
    sim.setShapeColor(box_handle, None, sim.colorcomponent_ambient_diffuse, color)
    sim.setObjectInt32Param(box_handle, sim.objintparam_visibility_layer, 1)
    
    # Make it static (1) so it behaves like a heavy weight sitting locked in place on the floor
    sim.setObjectInt32Param(box_handle, sim.shapeintparam_static, 1) 
    sim.setObjectInt32Param(box_handle, sim.shapeintparam_respondable, 1)
    
    sim.resetDynamicObject(box_handle)
    return box_handle

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
    tetromino = TetrominoGenerator(sim)
    base_pos: list[int] = sim.getObjectPosition(robot.simRobot, -1)
    offset_x = 0.5
    box_spacing = 0.3
    boxes = [
        create_sorting_box(sim, position=[base_pos[0] + offset_x,  base_pos[1] - (1.5 * box_spacing), 0.0], color=[1, 1, 0]),   # Square Box (Yellow)
        create_sorting_box(sim, position=[base_pos[0] + offset_x,  base_pos[1] - (0.5 * box_spacing), 0.0], color=[1, 0, 0]),   # Line Box (Red)
        create_sorting_box(sim, position=[base_pos[0] + offset_x,  base_pos[1] + (0.5 * box_spacing) + 0.03, 0.0], color=[1, 0.5, 0]), # L Box (Orange)
        create_sorting_box(sim, position=[base_pos[0] + offset_x,  base_pos[1] + (1.5 * box_spacing) + 0.03, 0.0], color=[0, 1, 0])   # S Box (Green)
    ]
    # TODO: refactor this
    box_index = 0
    try:
        while is_running:
            # AI / control logic:
            feed_manager.next_shape()
            # time.sleep(2)
            feed_manager.start_band()
            # feed_manager.next_cube()
            time.sleep(2)
            feed_manager.stop_band()
            time.sleep(0.5)
            feed_manager.pick_cube()
            current_joints = robot.ReadJointPosition()
    
            # 2. Force ONLY the base joint (joint 1) to swing over toward the box.
            # Leave the other 5 joints exactly where they are right now.
            # Box 3 is on the positive Y side, so let's aim the base around 45.0 degrees.
            escape_joints = [90.0, current_joints[1], current_joints[2], current_joints[3], current_joints[4], current_joints[5]]
            
            # Use your class's joint movement function to smoothly pivot the waist
            robot.MoveJ(escape_joints, speed=30)
            box_pos = feed_manager.robot.GetObjectPosition2(boxes[box_index % 4])
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