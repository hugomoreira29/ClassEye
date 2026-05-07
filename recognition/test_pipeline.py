# recognition/test_pipeline.py
import os
from recognize_faces import recognize_students

def test():
    # Define the path to your test classroom image
    # Using relative paths assuming you run this from inside the recognition/ folder
    test_image_path = "../input/classroom_images/test3.jpg"
    
    # Verify the test image actually exists before running
    if not os.path.exists(test_image_path):
        print(f"❌ Error: Test image not found at '{test_image_path}'.")
        print("Please create the folders and add a test image.")
        return

    print("🚀 Starting ClassEye Face Recognition Pipeline...")
    print("-" * 50)
    
    # Run the main recognition function
    present_students = recognize_students(test_image_path)
    
    print("-" * 50)
    print("Pipeline Execution Complete!")
    print(f"Final Attendance List: {present_students}")
    print("  Check '../output/processed_images/' to see the drawn bounding boxes.")

if __name__ == "__main__":
    test()