import streamlit as st
import requests
import json
from PIL import Image
import io

# Config
API_URL = "http://localhost:8000"

st.set_page_config(page_title="Nova Reel Marketing Studio", layout="wide", page_icon="🎬")

# Custom CSS for Blue & White Premium Look
st.markdown("""
    <style>
    .main {
        background-color: #f8fafc;
        color: #1e293b;
    }
    .stButton>button {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        padding: 0.6rem 2.5rem;
        border-radius: 0.75rem;
        font-weight: 700;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.2);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.3);
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%);
    }
    .stTextInput>div>div>input {
        background-color: white;
        color: #1e293b;
        border: 2px solid #e2e8f0;
        border-radius: 0.5rem;
    }
    .stTextInput>div>div>input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    h1, h2, h3 {
        color: #1e3a8a !important;
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
    }
    .status-card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 1.25rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
    }
    .instruction-box {
        background-color: #eff6ff;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 Nova Reel Marketing Studio")
st.markdown("### Elevate your brand with AI-powered cinematic assets.")
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
    
    # Provider Selection
    provider = st.sidebar.selectbox("Select Provider", ["Amazon Bedrock", "Google Cloud"], index=0)
    provider_key = "amazon" if provider == "Amazon Bedrock" else "google"
    
    selected_template_key = st.sidebar.selectbox("Select Template", list(templates.keys()))
    current_template = templates[selected_template_key]
    
    st.sidebar.info(f"**Type**: {current_template['type'].upper()}\n\n{current_template['description']}")

    # Setup Instructions
    with st.sidebar.expander("🛠️ Setup Instructions (CLI)"):
        st.markdown("""
        **AWS IAM Setup:**
        ```bash
        # Create Output Bucket
        aws s3 mb s3://nova-reel-out
        
        # Attach permissions
        # bedrock:InvokeModel
        # s3:PutObject
        ```
        **Model Access:**
        Enable 'Nova Reel' in US-East-1.
        """)

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
        
        payload_data = {
            "template_id": selected_template_key,
            "product_name": product_name,
            "params": json.dumps(params),
            "provider": provider_key
        }
        
        files = None
        if uploaded_image:
            files = {"image": (uploaded_image.name, uploaded_image, uploaded_image.type)}
            
        status_placeholder = st.empty()
        with status_placeholder.container():
             st.markdown('<div class="status-card">', unsafe_allow_html=True)
             with st.spinner(f"Generating {current_template['type']}..."):
                try:
                    # Send as Form Data (data=) + Files
                    res = requests.post(f"{API_URL}/{endpoint}", data=payload_data, files=files)
                    
                    if res.status_code == 200:
                        data = res.json()
                        st.success("✨ Generation Initiated!")
                        
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.subheader("Results")
                            if current_template['type'] == 'video':
                                st.info(f"Job ID: `{data.get('invocationArn', 'N/A')}`")
                                st.warning("Video generation is asynchronous. Check S3 output for results.")
                                # Simulate preview if possible or show path
                                st.code(f"Output Path: {data.get('s3_output', 'Pending...')}", language="bash")
                            else:
                                if "images" in data:
                                    st.image(data['images'], caption=f"Generated {product_name}")
                        
                        with col2:
                            st.subheader("Metadata")
                            st.json(data)
                        
                    else:
                        st.error(f"❌ Error: {res.text}")
                        st.json(res.json() if res.headers.get("content-type") == "application/json" else {"detail": res.text})
                        
                except Exception as e:
                    st.error(f"☢️ Failed to request: {e}")
             st.markdown('</div>', unsafe_allow_html=True)

