import os
import cv2
import face_recognition

def load_known_faces(dataset_path=None):
    if dataset_path is None:
        dataset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dataset")
    """
    Reads all student folders, loads images, generates face encodings, 
    and returns lists of encodings and corresponding names.
    
    Args:
        dataset_path (str): Relative path to the dataset folder.
        
    Returns:
        tuple: (known_face_encodings, known_student_names)
    """
    known_encodings = []
    known_names = []

    # Check if the dataset directory exists
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset directory '{dataset_path}' not found.")
        return known_encodings, known_names

    # Iterate through each student's folder in the dataset
    for student_name in os.listdir(dataset_path):
        student_folder = os.path.join(dataset_path, student_name)

        # Skip if it's not a directory
        if not os.path.isdir(student_folder):
            continue

        # Process each image in the student's folder
        for filename in os.listdir(student_folder):
            filepath = os.path.join(student_folder, filename)

            # Load image
            img = cv2.imread(filepath)
            if img is None:
                print(f"Warning: Could not load '{filepath}'. Skipping.")
                continue

            # Convert BGR to RGB for face_recognition
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # Generate face encodings
            encodings = face_recognition.face_encodings(rgb_img)

            # Ensure at least one face was found in the image
            if len(encodings) > 0:
                # We assume the first face found belongs to the student
                known_encodings.append(encodings[0])
                known_names.append(student_name)
            else:
                print(f"Warning: No face found in '{filepath}'. Skipping.")

    return known_encodings, known_names