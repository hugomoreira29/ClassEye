import cv2
import os
import time
from recognize_faces import recognize_students

def take_single_attendance():
    print("Initializing camera...")
    
    # 1. Open the camera
    video_capture = cv2.VideoCapture(0)

    if not video_capture.isOpened():
        print("Error: Could not open camera.")
        return []

    # 2. Wait 2 seconds for the camera sensor to adjust to the room's lighting
    print("Adjusting camera lighting...")
    time.sleep(2) 

    # 3. Take a single picture
    print("📸 Taking picture...")
    ret, frame = video_capture.read()

    # 4. Shut down the camera IMMEDIATELY so it isn't wasting Pi resources
    video_capture.release()
    cv2.destroyAllWindows()

    if not ret:
        print("Error: Failed to grab a picture.")
        return []

    # 5. Save the image temporarily
    temp_image_path = "../input/classroom_images/single_capture.jpg"
    cv2.imwrite(temp_image_path, frame)

    # 6. Run the recognition pipeline on that saved image
    print("🔍 Processing faces...")
    present_students = recognize_students(temp_image_path)

    # 7. Print final results
    print("-" * 40)
    print("Attendance Check Complete!")
    print(f"Present Students: {present_students}")
    print("-" * 40)
    
    # Return the list so other modules can use it later
    return present_students

if __name__ == "__main__":
    # Ensure the input directory exists
    if not os.path.exists("../input/classroom_images/"):
        os.makedirs("../input/classroom_images/")
        
    # Run the function once and stop
    take_single_attendance()