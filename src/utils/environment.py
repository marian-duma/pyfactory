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

def create_boxes(sim, base_pos):
    offset_x = 0.5
    box_spacing = 0.3
    return [
        create_sorting_box(sim, position=[base_pos[0] + offset_x,  base_pos[1] - (1.5 * box_spacing), 0.0], color=[1, 1, 0]),   # Square Box (Yellow)
        create_sorting_box(sim, position=[base_pos[0] + offset_x,  base_pos[1] - (0.5 * box_spacing), 0.0], color=[1, 0, 0]),   # Line Box (Red)
        create_sorting_box(sim, position=[base_pos[0] + offset_x,  base_pos[1] + (0.5 * box_spacing) + 0.03, 0.0], color=[1, 0.5, 0]), # L Box (Orange)
        create_sorting_box(sim, position=[base_pos[0] + offset_x,  base_pos[1] + (1.5 * box_spacing) + 0.03, 0.0], color=[0, 1, 0])   # S Box (Green)
    ]

def init_env():
    pass