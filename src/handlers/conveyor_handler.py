from coppeliasim_zmqremoteapi_client import RemoteAPIClient

class ConveyorHandler:
    """
    Handles communication with a conveyor belt model in CoppeliaSim.
    Uses the '__ctrl__' custom data buffer to set velocity or position.
    """
    def __init__(self, sim, conveyor_name: str):
        self._sim = sim
        self._handle = self._sim.getObject(conveyor_name)
        self.sensor = self._sim.getObject('/conveyorSensor')
        self.is_stopped = False
        self.start()
        if self._handle == -1:
            raise ValueError(f"Conveyor '{conveyor_name}' not found in scene.")

    def set_velocity(self, velocity: float):
        """
        Sets the target velocity of the conveyor.
        :param velocity: meters per second (m/s)
        """
        ctrl_data = {'vel': velocity}
        packed_data = self._sim.packTable(ctrl_data)
        
        self._sim.setBufferProperty(
            self._handle, 
            'customData.__ctrl__', 
            packed_data
        )

    def set_position(self, position: float):
        """
        Sets the target position of the conveyor.
        :param position: target distance in meters
        """
        ctrl_data = {'pos': position}
        packed_data = self._sim.pack_table(ctrl_data)
        
        self._sim.setBufferProperty(
            self._handle, 
            'customData.__ctrl__', 
            packed_data
        )
    def should_stop(self):
        # Read the sensor
        res, dist, pt, obj_handle, normal = self.read_sensor()
        return res > 0

    def read_sensor(self):
        return self._sim.readProximitySensor(self.sensor)

    def get_cube_position(self):
        res, dist, pt, obj_handle, normal = self.read_sensor()
        if res > 0:
            # 2. Get the sensor's current position and orientation matrix
            # (This matrix describes where the sensor is in the world)
            matrix = self._sim.getObjectMatrix(self.sensor, -1)
            
            # 3. Multiply the local point 'pt' by the sensor's matrix 
            # to get the point in World Coordinates
            world_pt = self._sim.multiplyVector(matrix, pt)
            
            return world_pt  # Returns [X, Y, Z] in meters relative to the floor
        return None

    def get_state(self) -> dict:
        """
        Reads the current state (position/velocity) from the conveyor.
        :return: A dictionary containing the current state data.
        """
        # Use read_custom_table_data to get the '__state__' table
        try:
            return self._sim.read_custom_table_data(self._handle, '__state__')
        except Exception:
            return {}
    
    def start(self):
        """Helper method to start the conveyor."""
        self.set_velocity(0.1)
        self.is_stopped = False
    
    def stop(self):
        """Helper method to halt the conveyor."""
        self.set_velocity(0.0)
        self.is_stopped = True