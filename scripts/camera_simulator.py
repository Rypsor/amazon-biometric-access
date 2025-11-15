import requests
import base64
import sys
import cv2
import time

def capture_image_from_webcam():
    """
    Captures a single frame from the default webcam.
    Shows a 3-second countdown on the screen.
    Returns the captured frame as a bytes object.
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return None

    print("Preparing to capture photo. Look at the camera!")

    for i in range(3, 0, -1):
        print(f"Capturing in {i}...")
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            cap.release()
            return None

        # Display the countdown on the frame
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = str(i)
        text_size = cv2.getTextSize(text, font, 7, 8)[0]
        text_x = (frame.shape[1] - text_size[0]) // 2
        text_y = (frame.shape[0] + text_size[1]) // 2
        cv2.putText(frame, text, (text_x, text_y), font, 7, (0, 0, 255), 8, cv2.LINE_AA)

        cv2.imshow('Webcam - Press ESC to cancel', frame)
        if cv2.waitKey(1000) == 27: # 1000ms delay, check for ESC key
            print("Capture cancelled by user.")
            cap.release()
            cv2.destroyAllWindows()
            return None

    ret, frame = cap.read()
    cap.release()
    cv2.destroyAllWindows()

    if not ret:
        print("Error: Failed to capture final image.")
        return None

    print("Photo captured!")
    _, img_encoded = cv2.imencode('.jpg', frame)
    return img_encoded.tobytes()

def verify_access_with_image(api_gateway_url, image_bytes):
    """
    Sends the captured image to the access control system for verification.
    :param api_gateway_url: The URL of the API Gateway endpoint.
    :param image_bytes: The image data as a bytes object.
    """
    try:
        encoded_string = base64.b64encode(image_bytes).decode('utf-8')
        headers = {'Content-Type': 'application/json'}

        print("Sending image for verification...")
        response = requests.post(api_gateway_url, headers=headers, data=encoded_string)

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python camera_simulator.py <api_gateway_url>")
        sys.exit(1)

    API_GATEWAY_URL = sys.argv[1]

    image_data = capture_image_from_webcam()

    if image_data:
        verify_access_with_image(API_GATEWAY_URL, image_data)
