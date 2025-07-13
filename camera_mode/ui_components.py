import streamlit as st

def setup_page_config():
    st.set_page_config(
        page_title="Mistral Camera OCR",
        page_icon="📸",
        layout="wide"
    )

def render_custom_css():
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.2rem;
            font-weight: 400;
            color: #666;
            margin-bottom: 2rem;
        }
        .info-box {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #4c75a3;
        }
        .stButton>button {
            background-color: #4c75a3;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 0.3rem;
            font-weight: 500;
        }
        .stButton>button:hover {
            background-color: #3a5a80;
        }
        .image-thumbnail {
            max-width: 150px;
            max-height: 150px;
            border-radius: 8px;
            border: 2px solid #ddd;
            margin: 5px;
        }
        .camera-container {
            border: 2px dashed #ccc;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            margin: 20px 0;
        }
        .capture-button {
            background-color: #ff4444 !important;
            color: white !important;
            border-radius: 50% !important;
            width: 80px !important;
            height: 80px !important;
            font-size: 24px !important;
        }
        .image-gallery {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 20px 0;
        }
        .image-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 10px;
            position: relative;
        }
        .delete-btn {
            position: absolute;
            top: 5px;
            right: 5px;
            background-color: #ff4444;
            color: white;
            border: none;
            border-radius: 50%;
            width: 25px;
            height: 25px;
            font-size: 12px;
            cursor: pointer;
        }
        .accumulated-text-area {
            border: 2px solid #4c75a3;
            border-radius: 8px;
            background-color: #f8f9fa;
        }
        .ocr-results-header {
            background: linear-gradient(90deg, #4c75a3, #5a84b8);
            color: white;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

def render_header():
    st.markdown('<p class="main-header">📸 Mistral Camera OCR</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Capture images with your camera and extract text using Mistral AI</p>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ How to use this app", expanded=False):
        st.markdown("""
        1. **Enter your Mistral API Key** (or set MISTRAL_API_KEY environment variable)
        2. **Click "Take a photo"** to activate your device's camera
        3. **Point at your document** and capture the image
        4. **Watch the text appear** automatically in the results area
        5. **Take more photos** to add text from additional pages
        6. **Download your results** as a Markdown file when done
        """)

def render_status_message(message: str, status_type: str = "info"):
    if status_type == "success":
        st.success(message)
    elif status_type == "error":
        st.error(message)
    elif status_type == "warning":
        st.warning(message)
    else:
        st.info(message)