import cv2
import face_recognition

def detect_faces(image_path):
    """
    Loads an image, detects faces, draws bounding boxes using OpenCV, 
    and returns the face locations and the modified image.
    
    Args:
        image_path (str): The path to the image file.
        
    Returns:
        tuple: (list of face_locations, image array with bounding boxes drawn)
    """
    # Load the image using OpenCV
    img = cv2.imread(image_path)
    
    # Handle gracefully if the image doesn't exist or is invalid
    if img is None:
        print(f"Error: Unable to load image at '{image_path}'.")
        return [], None

    # OpenCV uses BGR by default, but face_recognition requires RGB
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Find all face locations in the current image
    # Returns a list of tuples: (top, right, bottom, left)
    face_locations = face_recognition.face_locations(rgb_img)

    # Draw bounding boxes around detected faces
    for top, right, bottom, left in face_locations:
        cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 2)

    return face_locations, img