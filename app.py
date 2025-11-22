import streamlit as st
import requests
import base64
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Biometric Access Control",
    page_icon="🔒",
    layout="centered"
)

def verify_access(api_url, image_bytes):
    """Sends the image to the API Gateway for verification."""
    # Ensure URL ends with /access
    if not api_url.endswith('/access'):
        verify_url = f"{api_url.rstrip('/')}/access"
    else:
        verify_url = api_url

    try:
        # Convert bytes to base64 string
        encoded_string = base64.b64encode(image_bytes).decode('utf-8')
        headers = {'Content-Type': 'application/json'}

        print(f"Sending verification request to: {verify_url}")

        with st.spinner('Verifying identity...'):
            response = requests.post(verify_url, headers=headers, data=encoded_string)

        print(f"Received status code: {response.status_code}")
        return response

    except requests.exceptions.RequestException as e:
        print(f"Request Exception: {e}")
        st.error(f"Connection Error: {str(e)}")
        return None
    except Exception as e:
        print(f"General Exception: {e}")
        st.error(f"An error occurred: {str(e)}")
        return None

def register_employee(api_url, image_bytes, first_name, last_name, cedula, city):
    """Sends employee data to the API Gateway for registration."""
    # Ensure URL ends with /register
    if not api_url.endswith('/register'):
        register_url = f"{api_url.rstrip('/')}/register"
    else:
        register_url = api_url

    try:
        encoded_image = base64.b64encode(image_bytes).decode('utf-8')
        payload = {
            "image": encoded_image,
            "firstName": first_name,
            "lastName": last_name,
            "cedula": cedula,
            "city": city
        }
        headers = {'Content-Type': 'application/json'}

        print(f"Sending registration request to: {register_url}")

        with st.spinner('Registering employee...'):
            response = requests.post(register_url, json=payload, headers=headers)

        print(f"Received status code: {response.status_code}")
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None

def main():
    st.title("🔒 Biometric Access Control")
    st.markdown("### Identity Verification System")

    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        default_url = os.getenv("API_GATEWAY_URL", "")
        # Helper text clarifying the base URL
        api_url = st.text_input(
            "API Gateway Base URL",
            value=default_url,
            help="Enter the base URL (e.g. https://xyz.execute-api.us-east-1.amazonaws.com/dev)"
        )

        if not api_url:
            st.warning("⚠️ Please set API_GATEWAY_URL (Base URL) in .env or enter it above.")

        st.divider()
        st.header("Mode")
        mode = st.radio("Select Action:", ["Verify Access", "Register Employee"])

    if not api_url:
        st.info("Please configure the API Gateway URL in the sidebar to proceed.")
        return

    # --- VERIFY ACCESS MODE ---
    if mode == "Verify Access":
        st.subheader("User Verification")

        img_file_buffer = st.camera_input("Take a photo to request access", key="verify_cam")

        if img_file_buffer is not None:
            bytes_data = img_file_buffer.getvalue()

            if st.button("Verify Access", type="primary", use_container_width=True):
                response = verify_access(api_url, bytes_data)

                if response is not None:
                    status_code = response.status_code
                    try:
                        response_data = response.json()
                    except:
                        response_data = {"message": response.text}

                    st.divider()
                    if status_code == 200:
                        st.success(f"✅ Access Granted")
                        st.json(response_data)
                    elif status_code == 403:
                        st.error(f"⛔ Access Denied")
                        st.warning(f"Reason: {response_data.get('message', 'Unknown')}")
                    else:
                        st.warning(f"⚠️ Status: {status_code}")
                        st.info(f"Response: {response_data}")
                else:
                    st.error("Failed to get a response from the server.")

    # --- REGISTER EMPLOYEE MODE ---
    elif mode == "Register Employee":
        st.subheader("New Employee Registration")

        # REMOVED st.form wrapper to allow easier state management and interaction
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name")
            cedula = st.text_input("ID Document (Cedula)")
        with col2:
            last_name = st.text_input("Last Name")
            city = st.selectbox("City", ["Medellin", "Bogota", "Cali", "Cartagena"])

        st.markdown("#### Capture Photo")
        reg_img_buffer = st.camera_input("Take a photo for registration", key="register_cam")

        # Final Register Action
        if st.button("Register Employee", type="primary", use_container_width=True):
            # Validation logic
            if not (first_name and last_name and cedula and city):
                 st.error("Please fill in all text fields (Name, Last Name, ID, City).")
            elif reg_img_buffer is None:
                 st.error("Please take a photo.")
            else:
                bytes_data = reg_img_buffer.getvalue()
                response = register_employee(api_url, bytes_data, first_name, last_name, cedula, city)

                if response is not None:
                    status_code = response.status_code
                    try:
                        response_data = response.json()
                    except:
                        response_data = {"message": response.text}

                    if status_code == 200:
                        st.balloons()
                        st.success("✅ Employee Registered Successfully!")
                        st.json(response_data)
                    else:
                        st.error(f"❌ Registration Failed (Status: {status_code})")
                        st.json(response_data)

if __name__ == "__main__":
    main()
