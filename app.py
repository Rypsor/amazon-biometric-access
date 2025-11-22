import streamlit as st
import requests
import base64
import os
import boto3
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Biometric Access Control",
    page_icon="🔒",
    layout="centered"
)

def get_base_url(api_url):
    """Cleans the API URL to get the base endpoint (without /access or /register)."""
    api_url = api_url.rstrip('/')
    if api_url.endswith('/access'):
        return api_url[:-7]
    if api_url.endswith('/register'):
        return api_url[:-9]
    return api_url

def verify_access(api_url, image_bytes):
    """Sends the image to the API Gateway for verification."""
    base_url = get_base_url(api_url)
    verify_url = f"{base_url}/access"

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
    base_url = get_base_url(api_url)
    register_url = f"{base_url}/register"

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

def get_dashboard_image(metric_widget_json):
    """Fetches a metric widget image from CloudWatch."""
    try:
        cw = boto3.client('cloudwatch')
        response = cw.get_metric_widget_image(MetricWidget=metric_widget_json)
        return response['MetricWidgetImage']
    except Exception as e:
        st.error(f"Failed to load dashboard: {str(e)}")
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
        mode = st.radio("Select Action:", ["Verify Access", "Register Employee", "Dashboard"])

    # --- DASHBOARD MODE (No API URL needed technically, but keeps flow consistent) ---
    if mode == "Dashboard":
        st.subheader("System Monitoring")
        st.info("Metrics are pulled directly from CloudWatch.")

        # Define Widgets
        # Widget 1: Access Attempts
        widget_access = {
            "view": "timeSeries",
            "stacked": False,
            "metrics": [
                [ "BiometricAccessControl", "AccessAttempts", "Status", "Granted", { "stat": "Sum", "period": 3600, "label": "Granted" } ],
                [ "...", "Denied", { "stat": "Sum", "period": 3600, "label": "Denied" } ]
            ],
            "width": 600,
            "height": 400,
            "start": "-PT24H",
            "end": "P0D",
            "title": "Access Attempts (Last 24 Hours)"
        }

        # Widget 2: Registrations
        widget_registrations = {
            "view": "singleValue",
            "metrics": [
                [ "BiometricAccessControl", "EmployeeRegistrations", { "stat": "Sum", "period": 86400, "label": "Total Registrations" } ]
            ],
            "width": 600,
            "height": 200,
            "start": "-P7D",
            "end": "P0D",
            "title": "Registrations (Last 7 Days)"
        }

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Access Attempts")
            img_access = get_dashboard_image(json.dumps(widget_access))
            if img_access:
                st.image(img_access)

        with col2:
            st.markdown("#### Employee Registrations")
            img_reg = get_dashboard_image(json.dumps(widget_registrations))
            if img_reg:
                st.image(img_reg)

        if st.button("Refresh Metrics"):
            # Handle compatibility for older Streamlit versions on Python 3.7
            if hasattr(st, 'rerun'):
                st.rerun()
            else:
                st.experimental_rerun()

        return

    # Validation for other modes that need API URL
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
