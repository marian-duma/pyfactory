class CubeGenerator:
    def __init__(self, sim, spawn_rate=5.0, spawn_position=None):
        """Initializes the generator and grabs the template."""
        self.sim = sim
        self.spawn_rate = spawn_rate
        
        self.template_cube = self.sim.getObject('/cube')
        self.cubes = []
        # Invert z axis
        if spawn_position is None:
            self.spawn_position = sim.getObjectPosition(self.template_cube, -1)
            self.spawn_position[2] *= -1
        else:
            self.spawn_position = spawn_position
        
        self.last_spawn_time = self.sim.getSimulationTime()


    def spawn_cube(self):
        """Internal helper to handle the CoppeliaSim cloning math."""
        new_cubes = self.sim.copyPasteObjects([self.template_cube], 0)
        new_cube_handle = new_cubes[0]

        self.cubes.append(new_cube_handle)
        
        self.sim.setObjectPosition(new_cube_handle, -1, self.spawn_position)
        
        # Make the object visible, dynamic and responsive
        self.sim.setObjectInt32Param(new_cube_handle, self.sim.objintparam_visibility_layer, 1)
        self.sim.setObjectInt32Param(new_cube_handle, self.sim.shapeintparam_static, 0)
        self.sim.setObjectInt32Param(new_cube_handle, self.sim.shapeintparam_respondable, 1)
        self.sim.resetDynamicObject(new_cube_handle)