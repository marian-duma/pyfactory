from coppeliasim_zmqremoteapi_client import RemoteAPIClient

class ConveyorHandler:
    """
    Handles communication with a conveyor belt model in CoppeliaSim.
    Uses the '__ctrl__' custom data buffer to set velocity or position.
    """
    def __init__(self, sim, conveyor_name: str):
        self._sim = sim
        self._handle = self._sim.getObject(conveyor_name)
        
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
    def stop(self):
        """Helper method to halt the conveyor."""
        self.set_velocity(0.0)