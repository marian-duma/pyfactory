import random
from .cube_generator import CubeGenerator

class TetrominoGenerator(CubeGenerator):
    def __init__(self, sim, spawn_rate=5.0, spawn_position=None):
        super().__init__(sim)
        
        self.block_size = 0.05 
        
        if spawn_position is None:
            self.spawn_position = self.sim.getObjectPosition(self.template_cube, -1)
            self.spawn_position[2] *= -1  # Preserve your original z inversion
        else:
            self.spawn_position = spawn_position
            
        self.last_spawn_time = self.sim.getSimulationTime()
        self.spawned_shapes = []

        # Define shape blueprints using local grid coordinates [X, Y]
        self.blueprints = {
            'square': [[0, 0], [1, 0], [0, 1], [1, 1]],
            'line':   [[0, 0], [1, 0], [2, 0], [3, 0]],
            'L':      [[0, 0], [0, 1], [0, 2], [1, 0]],
            'S':      [[0, 0], [1, 0], [1, 1], [2, 1]]
        }

    import random

    def spawn_random_tetromino(self):
        """Randomly chooses a tetromino type and a random color, then spawns it."""
        shape_type = random.choice(list(self.blueprints.keys()))
        
        # 1. Define the available colors (Tuned for your OpenCV HSV thresholds)
        color_palette = {
            "RED":    [1.0, 0.0, 0.0],
            "ORANGE": [1.0, 0.4, 0.0],  # 0.4 Green ensures it doesn't look Red to the camera
            "YELLOW": [1.0, 1.0, 0.0],
            "GREEN":  [0.0, 1.0, 0.0]
        }
        
        # 2. Pick a random color
        color_name, rgb_values = random.choice(list(color_palette.items()))
        
        # 3. Pass both to the builder method
        return self.spawn_tetromino(shape_type, color_name, rgb_values)

    def spawn_tetromino(self, shape_type, color_name=None, rgb_values=None):
        """Builds a composite tetromino shape out of individual template cubes."""
        if shape_type not in self.blueprints:
            print(f"Unknown shape: {shape_type}")
            return -1

        grid_coords = self.blueprints[shape_type]
        sub_cubes = []

        # 1. Clone and arrange the sub-cubes relative to the spawn origin
        for i, (gx, gy) in enumerate(grid_coords):
            new_cubes = self.sim.copyPasteObjects([self.template_cube], 0)
            cube_handle = new_cubes[0]
            sub_cubes.append(cube_handle)

            # Offset each block relative to the main spawn position
            local_x = self.spawn_position[0] + (gx * self.block_size)
            local_y = self.spawn_position[1] + (gy * self.block_size)
            local_z = self.spawn_position[2]

            self.sim.setObjectPosition(cube_handle, -1, [local_x, local_y, local_z])

        # 2. Fuse the blocks into a single compound object
        compound_handle = self.sim.groupShapes(sub_cubes)

        # --- THE COLOR & VISION UPDATES ---

        # Fallback: If someone calls spawn_tetromino("L") directly without a color, 
        # it will use your original default colors.
        if rgb_values is None:
            default_colors = {
                'square': [1.0, 1.0, 0.0],
                'line':   [1.0, 0.0, 0.0],
                'L':      [1.0, 0.4, 0.0], 
                'S':      [0.0, 1.0, 0.0]
            }
            rgb_values = default_colors.get(shape_type, [1.0, 1.0, 1.0])
            color_name = "Default"

        # Apply the chosen Diffuse/Ambient color
        self.sim.setShapeColor(compound_handle, None, self.sim.colorcomponent_ambient_diffuse, rgb_values)
        
        # CRITICAL OPENCV FIX: Force the Specular (Shininess) component to Black (0,0,0)
        # This prevents the white glare that was ruining your Saturation Map!
        self.sim.setShapeColor(compound_handle, None, self.sim.colorcomponent_specular, [0.0, 0.0, 0.0])

        # ----------------------------------

        # Enable full physics on the combined compound group
        self.sim.setObjectInt32Param(compound_handle, self.sim.objintparam_visibility_layer, 1)
        self.sim.setObjectInt32Param(compound_handle, self.sim.shapeintparam_static, 0)
        self.sim.setObjectInt32Param(compound_handle, self.sim.shapeintparam_respondable, 1)
        
        # Give the whole group mass and refresh the physics simulation state
        self.sim.setShapeMass(compound_handle, 0.4) 
        self.sim.resetDynamicObject(compound_handle)

        self.spawned_shapes.append(compound_handle)
        
        # print(f"Generator: Built a {color_name} {shape_type}!")
        return compound_handle