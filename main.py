import streamlit as st
import os
from PIL import Image
import pandas as pd
import mimetypes
from process_docs import show_document_upload
from chat import generate
import json
os.environ["FIREWORKS_API_KEY"]="fw_3ZYw86Am1N66XjT14X2nzvSH"
# Configure Streamlit page
st.set_page_config(page_title="Consultation Agent", layout="wide")
import base64
import docx
import base64
from pathlib import Path
import mimetypes
import PyPDF2
import markdown
from PIL import Image
import io

# First, import required libraries at the top of your file
def get_file_type(file_path):
    """Determine the type of file based on its extension."""
    return Path(file_path).suffix.lower()[1:]
def create_file_viewer(file_path):
    """Create a download button for files using Streamlit's native download button."""
    try:
        # Read file as bytes
        with open(file_path, "rb") as file:
            file_bytes = file.read()
            
        # Get file name
        file_name = Path(file_path).name
        
        # Get MIME type
        mime_type = mimetypes.guess_type(file_path)[0]
        if mime_type is None:
            mime_type = 'application/octet-stream'
            
        # Create download button with custom styling
        download_button_style = """
        <style>
            .stDownloadButton > button {
                background-color: #d35e3b ;
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 0.25rem;
                border: none;
                cursor: pointer;
                width: 100%;
            }
            .stDownloadButton > button:hover {
                background-color: #edaf3c;
                color: white;
            }
        </style>
        """
        st.markdown(download_button_style, unsafe_allow_html=True)
        ID=generate_numeric_id()
     
        # Create the download button
        st.download_button(
            label=f"Download {ID}-{file_name}",
            data=file_bytes,
            file_name=file_name,
            mime=mime_type,
        )
        
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")


import random
import string

def generate_numeric_id():
    """Generate a random 4-digit numeric ID."""
    return str(random.randint(1000, 9999))

def display_file_paths(paths):
    """Display file paths with expandable viewers containing download buttons."""
    if paths:  # Check if there are any paths to display
        st.markdown("### Referenced Documents")
        for path in paths:
            with st.expander(f"📄 {Path(path).name}"):
                create_file_viewer(path)


def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            return f"data:image/png;base64,{encoded_string}"
    except Exception as e:
        return None
        
# Initialize session state for login and messages
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'file_paths' not in st.session_state:
    st.session_state.file_paths = []
def login():
    # Create three columns, using the middle one for content
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        base64_image = get_base64_image("Images/logo.png" )
        # Center the image using HTML
        st.markdown(
            f"""
            <div style="display: flex; justify-content: center;">
          <img src="{base64_image}" width="200" alt="Consultation Agent">
            </div>
            <div style="text-align: center; margin-bottom: 20px;">
                <p>Consultation Agent</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<h1 style='text-align: center;'>Login</h1>", unsafe_allow_html=True)

        # Add some spacing
        st.markdown("<br>", unsafe_allow_html=True)

        # Login form
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Sign In", use_container_width=True):
                
            # Center the messages
            if username == "admin" and password == "admin123":
                st.session_state.logged_in = True
                st.markdown(
                    "<div style='text-align: center;'>"
                    "<p style='color: #198754;'>Logged in successfully!</p>"
                    "</div>",
                    unsafe_allow_html=True
                )
                
                st.rerun()
            else:
                st.session_state.logged_in = False
                st.markdown(
                    "<div style='text-align: center;'>"
                    "<p style='color: red;'>Invalid Credentials!</p>"
                    "</div>",
                    unsafe_allow_html=True
                )

    
def main():
    st.sidebar.image("Images/logo.png",caption="Consultation Agent")
    st.sidebar.subheader("Navigation")
    page = st.sidebar.selectbox("Select Page", ["Chat Interface", "Document Upload"])

    if page == "Chat Interface":
        show_chat_interface()
    elif page== "Document Upload" :
        show_document_upload()

def show_chat_interface():
   
    st.title("Chat Interface")
    
    # Initialize content placeholder for streaming
    content_placeholder = st.empty()
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.write(message["content"])
            else:
                st.markdown(message["content"]["response"])
                # Display associated files if they exist
                if st.session_state.file_paths:
                    display_file_paths(st.session_state.file_paths)
    
    # Handle new chat input
    if prompt := st.chat_input("What would you like to know?"):
        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate and display streaming response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            content = ""
            
            try:
                print("before")
                # Generate response
                response = generate(prompt)
                print("after")
                # Store file paths in session state
                if response['paths']:
                    st.session_state.file_paths = response['paths']
                
                # Display file download buttons
                display_file_paths(response['paths'])

                # Stream the response
                for chunk in response['response']:
                    if hasattr(chunk.choices[0].delta, 'content'):
                        token = chunk.choices[0].delta.content
                        if token:
                            content += token
                            response_placeholder.markdown(content)
                            
                final_response = {"response": content}
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_response
                })
                
            except Exception as e:
                st.error(f"An error occurred while generating the response. Please try again.")
                print(e)

if not st.session_state.logged_in:
    login()
else:
    main()
