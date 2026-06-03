# src/stations/vision.py
import cv2
import numpy as np

class ColorDetector:
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
        img, res = self.sim.getVisionSensorImg(self.camera_handle)
        if not img: return "NONE"

        # 1. Convert to OpenCV BGR format
        frame = np.frombuffer(img, dtype=np.uint8).reshape((res[1], res[0], 3))
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame = cv2.flip(frame, 0)

        # 2. Convert BGR to HSV
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 3. Sample the center of the image
        height, width, _ = hsv_frame.shape
        roi = hsv_frame[height//2-5:height//2+5, width//2-5:width//2+5]
        avg_hsv = cv2.mean(roi)
        
        hue = avg_hsv[0] # Hue is 0-180 in OpenCV
        sat = avg_hsv[1] # Saturation 0-255
        val = avg_hsv[2] # Brightness 0-255

        # 4. Logic based on the Hue Degree
        # Values may need slight tuning based on your specific light
        if val < 50: return "BLACK/NONE" # Too dark
        
        if 35 < hue < 85:
            return "GREEN"
        elif 22 < hue <= 35:
            return "YELLOW"
        elif 10 < hue <= 22:
            return "ORANGE"
        elif hue <= 10 or hue > 160:
            return "RED"
        
        return "UNKNOWN"