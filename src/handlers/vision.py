# src/stations/vision.py
import cv2
import numpy as np

class OpenCVDetector:
    def __init__(self, sim):
        self.sim = sim
        self.camera_handle = self.sim.getObject('/visionSensor')

    def get_color(self):
        # 1. Get raw image from sim
        # img is a byte array, res is [width, height]
        img, res = self.sim.getVisionSensorImg(self.camera_handle)
        
        if not img:
            return "NONE"

        # 2. Convert bytes to NumPy array and reshape
        # CoppeliaSim images are usually RGB; OpenCV uses BGR
        frame = np.frombuffer(img, dtype=np.uint8)
        frame = frame.reshape((res[1], res[0], 3))
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Optional: Flip image if it appears upside down in OpenCV
        frame = cv2.flip(frame, 0)

        # 3. Use OpenCV to find the color
        # We'll look at a small 10x10 square in the center to avoid edges
        height, width, _ = frame.shape
        center_roi = frame[height//2-5:height//2+5, width//2-5:width//2+5]
        avg_color = cv2.mean(center_roi) # Returns (Blue, Green, Red)

        # 4. Logic based on BGR averages
        b, g, r = avg_color[0], avg_color[1], avg_color[2]
        
        print(f"R: {r}, G: {g}, B: {b}") # Add this to see the "flicker" values

        # # Show the "Robot Vision" window (Great for debugging!)
        # cv2.imshow("Robot View", frame)
        # cv2.waitKey(1) 

        if r > 150 and g < 100: return "RED"
        if b > 150 and r < 100: return "BLUE"
        if g > 150 and r < 100: return "GREEN"
        
        return "UNKNOWN"
    
    def get_color2(self):
        """Finds the object in the frame and determines its color."""
        img, res = self.sim.getVisionSensorImg(self.camera_handle)
        if not img: 
            return "NONE"

        # 1. Convert to OpenCV formats
        frame = np.frombuffer(img, dtype=np.uint8).reshape((res[1], res[0], 3))
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame = cv2.flip(frame, 0)
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 2. Find the block using the Saturation Channel
        saturation_channel = hsv_frame[:, :, 1] 
        _, thresh = cv2.threshold(saturation_channel, 50, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Debug Window (Optional)
        # cv2.imshow("Saturation Map", thresh)
        # cv2.waitKey(1)

        # 3. If no blocks are found, return NONE
        if not contours:
            return "NONE (NO OBJECT)"

        # 4. Grab the largest object (ignores tiny noise/dust)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # 5. Create a mask tightly wrapping the shape
        mask = np.zeros(hsv_frame.shape[:2], np.uint8)
        cv2.drawContours(mask, [largest_contour], -1, 255, -1)
        
        # 6. Calculate the average color ONLY inside that mask
        hue, sat, val, _ = cv2.mean(hsv_frame, mask=mask)
        
        # print(f"DEBUG SHAPE COLOR: H={hue:.1f} | S={sat:.1f} | V={val:.1f}")

        # 7. Route to classification logic
        return self._classify_color(hue, sat, val)


    # ==========================================
    # Add this helper function to the same class
    # ==========================================
    def _classify_color(self, hue, sat, val):
        """Categorizes an HSV value into a string label."""
        # 1. Environment checks (Shadows and Glare)
        if val < 50: 
            return "BLACK/NONE"         # Too dark (Shadows)
        if sat < 15: 
            return "UNKNOWN (GRAY)"     # No color (Conveyor belt or glare)

        # 2. Hue checks (0-180 scale)
        if 35 < hue < 85:
            return "GREEN"
        elif 22 < hue <= 35:
            return "YELLOW"
        elif 11 < hue <= 22:
            return "ORANGE"
        elif hue <= 11 or hue > 160:
            return "RED"
        
        return "UNKNOWN"

class ShapeDetector(OpenCVDetector): # Inherit your previous vision class
    def __init__(self, sim):
        super().__init__(sim)
        # Camera parameters (Check these in Vision Sensor properties in Sim)
        self.resolution = [64, 64] 
        self.view_angle = 60 # Default is often 60 degrees
    
    def _pixel_to_world(self, cx, cy, res):
        # 1. Get Camera World State
        cam_matrix = self.sim.getObjectMatrix(self.camera_handle, -1)
        cam_pos = self.sim.getObjectPosition(self.camera_handle, -1)
        
        # 2. Calculate the 'Real World' size of one pixel
        # Assuming camera is looking straight down (Z-axis)
        import math
        fov_rad = self.view_angle * (math.pi / 180)
        
        # Distance from camera to conveyor belt
        # (Replace 0.15 with your actual belt height or detect it via proximity)
        z_dist = cam_pos[2] - 0.15 
        
        # Total width/height the camera sees at that distance
        view_width = 2 * z_dist * math.tan(fov_rad / 2)
        
        # 3. Scale pixel to meters (Relative to camera center)
        # Flip Y because image coords (0,0) is top-left, world is center
        rel_x = ((cx / res[0]) - 0.5) * view_width
        rel_y = (0.5 - (cy / res[1])) * view_width 
        
        # 4. Transform to absolute World Coordinates
        # (Simply add camera position if it's not rotated, 
        # otherwise use multiplyVector with cam_matrix)
        world_x = cam_pos[0] + rel_x
        world_y = cam_pos[1] + rel_y
        world_z = 0.15 # The height of the belt
        
        return [world_x, world_y, world_z]
    
    def get_shape_and_world_pos(self):
        img, res = self.sim.getVisionSensorImg(self.camera_handle)
        if not img: return None, None
        
        # 1. Image Pre-processing
        frame = np.frombuffer(img, dtype=np.uint8).reshape((res[1], res[0], 3))
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY)
        
        # 2. Find Contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 100: continue 
            
            # 1. Get Bounding Box info
            x, y, w, h = cv2.boundingRect(cnt)
            rect_area = w * h
            extent = float(area) / rect_area
            aspect_ratio = float(w) / h if h != 0 else 0
            
            # To handle vertical vs horizontal, always make ratio > 1
            if aspect_ratio < 1: aspect_ratio = 1 / aspect_ratio

            shape = "UNKNOWN"
            
            # --- TETROMINO LOGIC ---
            
            # 1. I-Shape: Very high aspect ratio (approx 4:1)
            if aspect_ratio > 2.5:
                shape = "I-PIECE"
            
            # 2. Square (O-Shape): Aspect ratio ~1 and very "full" (Extent > 0.9)
            elif aspect_ratio < 1.2 and extent > 0.85:
                shape = "SQUARE"
            
            # 3. L and Z Shapes: These have lower "Extent" (approx 0.75) 
            # because they have empty space in their bounding box.
            elif extent < 0.80:
                # Distinguish L vs Z using the "Convex Hull" or "Solidity"
                hull = cv2.convexHull(cnt)
                hull_area = cv2.contourArea(hull)
                solidity = float(area) / hull_area
                    
                # Z-pieces are usually more "hollow" relative to their hull
                if solidity < 0.85:
                    shape = "Z-PIECE"
                else:
                    shape = "L-PIECE"

            # --- CENTER CALCULATION (Image Space) ---
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
                # Now pass these to your _pixel_to_world function
                world_pos = self._pixel_to_world(cx, cy, res)
                return shape, world_pos
                
        return None, None