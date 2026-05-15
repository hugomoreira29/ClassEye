import os
import cv2
import face_recognition
import numpy as np

# Import functions from the other modules
from encode_faces import load_known_faces
from detect_faces import detect_faces

def recognize_students(image_path, tolerance=0.5):
    """
    Detects faces in a classroom image, compares them with known students,
    labels them, saves the processed image, and returns a list of unique names.
    
    Args:
        image_path (str): Path to the classroom image.
        
    Returns:
        list: Unique recognized student names (including 'Unknown').
    """
    _base = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(_base, "..", "dataset")
    output_dir   = os.path.join(_base, "..", "output", "processed_images")
    
    # 1. Load known student encodings and names
    print("Loading known faces...")
    known_encodings, known_names = load_known_faces(dataset_path)
    
    if not known_encodings:
        print("Error: No known faces were loaded. Cannot proceed with recognition.")
        return []

    # 2. Detect faces and get bounding boxes using detect_faces.py
    print(f"Analyzing classroom image: {image_path}")
    face_locations, img = detect_faces(image_path)
    
    if img is None or not face_locations:
        print("No faces detected or image is invalid.")
        return []

    # Convert the image to RGB for the encoding process
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # 3. Generate encodings for the newly detected faces
    face_encodings = face_recognition.face_encodings(rgb_img, face_locations)

    recognized_names = []

    # 4. Compare detected encodings with known encodings
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        
        # Default name if no match is found
        name = "Unknown"

        # Calculate face distances to find the best match
        face_distances = face_recognition.face_distance(known_encodings, face_encoding)
        
        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
            
            # Set a strict threshold (Default is 0.6. Lower = stricter)
            # 0.45 to 0.5 is usually a good sweet spot to prevent false positives
            TOLERANCE_THRESHOLD = tolerance

            if face_distances[best_match_index] <= TOLERANCE_THRESHOLD:
                name = known_names[best_match_index]
            else:
                name = "Unknown"

        recognized_names.append(name)

        # Draw a filled rectangle below the face for the name label
        cv2.rectangle(img, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
        
        # Add the recognized name (or "Unknown") as text
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(img, name, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)

    # 5. Save the processed image to the output folder
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename = os.path.basename(image_path)
    output_path = os.path.join(output_dir, f"processed_{filename}")
    
    cv2.imwrite(output_path, img)
    print(f"Processed image successfully saved to: {output_path}")

    # 6. Remove duplicate names using a set, then convert back to a list
    unique_recognized_names = list(set(recognized_names))

    return unique_recognized_names

# ==========================================
# Example usage (Uncomment to test locally)
# ==========================================
# if __name__ == "__main__":
#     classroom_image = "../input/classroom_images/class1.jpg"
#     present_students = recognize_students(classroom_image)
#     print("Attendance List:", present_students)