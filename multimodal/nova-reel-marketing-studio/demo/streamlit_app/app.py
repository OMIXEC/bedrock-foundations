import streamlit as st
import requests
import json
from PIL import Image
import io

# Config
API_URL = "http://localhost:8000"

st.set_page_config(page_title="Nova Reel Marketing Studio", layout="wide")

st.title("🎬 Nova Reel Marketing Studio")
st.markdown("Generate high-end marketing assets using **AWS Nova Reel** and **Google Veo/Gemini**.")

# Fetch Templates
@st.cache_data
def get_templates():
    try:
        res = requests.get(f"{API_URL}/templates")
        if res.status_code == 200:
            return res.json()
    except:
        return {}
    return {}

templates = get_templates()

if not templates:
    st.error("Could not connect to Backend API. Is it running?")
else:
    # Sidebar
    st.sidebar.header("Configuration")
    selected_template_key = st.sidebar.selectbox("Select Template", list(templates.keys()))
    current_template = templates[selected_template_key]
    
    st.sidebar.info(f"**Type**: {current_template['type'].upper()}\n\n{current_template['description']}")

    # Main Form
    with st.form("generation_form"):
        st.subheader("Product Details")
        product_name = st.text_input("Product Name", value="Luxury Perfume")
        
        # Dynamic Fields based on optional_params
        params = {}
        if "optional_params" in current_template:
            st.markdown("### Customization")
            cols = st.columns(2)
            i = 0
            for key, default_val in current_template["optional_params"].items():
                with cols[i % 2]:
                    params[key] = st.text_input(f"{key.replace('_', ' ').title()}", value=default_val)
                i += 1
                
        uploaded_image = st.file_uploader("Reference Product Image (Optional)", type=["jpg", "png"])
        
        submitted = st.form_submit_button("✨ Generate Asset")
        
    if submitted:
        endpoint = "generate/video" if current_template['type'] == 'video' else "generate/image"
        
        payload = {
            "template_id": selected_template_key,
            "product_name": product_name,
            "params": params
        }
        
        files = None
        if uploaded_image:
            files = {"image": (uploaded_image.name, uploaded_image, uploaded_image.type)}
            
        with st.spinner(f"Generating {current_template['type']}..."):
            try:
                # We need to send JSON data + Files. 
                # Requests handles multipart/form-data complexity.
                # But FastAPI expecting Pydantic model in 'request' field as JSON might be tricky with Multipart.
                # Standard pattern: Send logic params as Form fields if using UploadFile.
                # OR: Two step process.
                # FOR DEMO SIMPLICITY: We will JSON dump the payload into a form field called 'request_json' if file exists, 
                # or just use standard JSON body if no file.
                
                # Adapting Main.py to handle this might be needed. 
                # Let's assume for now we just send JSON for Text-driven generation.
                
                res = requests.post(f"{API_URL}/{endpoint}", json=payload)
                
                if res.status_code == 200:
                    data = res.json()
                    st.success("Generation Initiated!")
                    st.json(data)
                    
                    if "images" in data:
                        # Display Images
                        # Assuming data['images'] is list of base64 or URLs
                        st.image(data['images']) # Placeholder
                        
                else:
                    st.error(f"Error: {res.text}")
                    
            except Exception as e:
                st.error(f"Failed to request: {e}")

