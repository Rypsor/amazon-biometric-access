import requests
import base64
import sys

def simulate_camera(api_gateway_url, image_path):
    """
    Simulates a camera sending an image to the access control system.

    :param api_gateway_url: The URL of the API Gateway endpoint.
    :param image_path: The path to the image file to send.
    """
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

        headers = {'Content-Type': 'application/json'}
        response = requests.post(api_gateway_url, headers=headers, data=encoded_string)

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python camera_simulator.py <api_gateway_url> <image_path>")
        sys.exit(1)

    API_GATEWAY_URL = sys.argv[1]
    IMAGE_PATH = sys.argv[2]

    simulate_camera(API_GATEWAY_URL, IMAGE_PATH)
