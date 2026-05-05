import sys
import signal
import time

import utils.connection as connection

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

    # Object handlers:
    robot_handle = sim.getObject('/PioneerP3DX')
    left_motor = sim.getObject('/PioneerP3DX/leftMotor')
    right_motor = sim.getObject('/PioneerP3DX/rightMotor')

    print(f"{robot_handle=}")
    print(f"{left_motor=}")
    print(f"{right_motor=}")
    
    sim.stopSimulation()
    time.sleep(0.5)
    sim.startSimulation()
    
    print("Simulation started. Press CTRL+C to stop.")
    
    start_time = sim.getSimulationTime()
    
    try:
        while is_running:
            # AI / control logic:
            current_time = sim.getSimulationTime()
            elapsed_time = current_time - start_time

            if elapsed_time < 3.0:
                sim.setJointTargetVelocity(left_motor, MOTOR_SPEED)
                sim.setJointTargetVelocity(right_motor, MOTOR_SPEED)
            elif elapsed_time < 6.0:
                sim.setJointTargetVelocity(left_motor, -MOTOR_SPEED)
                sim.setJointTargetVelocity(right_motor, -MOTOR_SPEED)
            else:
                start_time = sim.getSimulationTime()

            client.step()

    except Exception as e:
        print(f"\nAn error occurred during execution: {e}")

    finally:
        try:
            sim.stopSimulation()
            print("Simulation stopped!")
        except Exception as e:
            print(f"Failed to stop simulation cleanly. ZMQ Socket state broken. {e}")
        sys.exit(0)

if __name__ == "__main__":
    main()