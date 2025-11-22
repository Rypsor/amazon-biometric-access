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
    try:
        # Convert bytes to base64 string
        encoded_string = base64.b64encode(image_bytes).decode('utf-8')
        headers = {'Content-Type': 'application/json'}

        with st.spinner('Verifying identity...'):
            response = requests.post(api_url, headers=headers, data=encoded_string)

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
        # Try to get URL from env var, otherwise allow user input
        default_url = os.getenv("API_GATEWAY_URL", "")
        api_url = st.text_input(
            "API Gateway URL",
            value=default_url,
            help="Enter the full Invoke URL ending in /access"
        )

        if not api_url:
            st.warning("⚠️ Please set API_GATEWAY_URL in .env or enter it above.")

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        # Native Streamlit Camera Input
        img_file_buffer = st.camera_input("Take a photo to request access")

    if img_file_buffer is not None:
        if not api_url:
            st.error("Please configure the API Gateway URL first.")
            return

        # Read bytes from the buffer
        bytes_data = img_file_buffer.getvalue()

        # Show the verification button
        if st.button("Verify Access", type="primary", use_container_width=True):
            response = verify_access(api_url, bytes_data)

            if response:
                status_code = response.status_code
                try:
                    response_data = response.json()
                except:
                    response_data = {"message": response.text}

                st.divider()
                st.subheader("Verification Result")

                if status_code == 200:
                    st.success(f"✅ Access Granted")
                    st.json(response_data)
                elif status_code == 403:
                    st.error(f"⛔ Access Denied")
                    st.warning(f"Reason: {response_data.get('message', 'Unknown')}")
                else:
                    st.warning(f"⚠️ Status: {status_code}")
                    st.info(f"Response: {response_data}")

if __name__ == "__main__":
    main()
