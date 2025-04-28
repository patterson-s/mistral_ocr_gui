import streamlit as st
import json
import os
import tempfile
import time
from mistralai import Mistral

# Set page configuration
st.set_page_config(
    page_title="Mistral OCR App",
    page_icon="📄",
    layout="wide"
)

# Custom CSS
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
</style>
""", unsafe_allow_html=True)

# Title and description
st.markdown('<p class="main-header">Mistral OCR Document Processor</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Extract text from PDF documents using Mistral AI\'s OCR capabilities</p>', unsafe_allow_html=True)

# Instructions
with st.expander("ℹ️ How to use this app", expanded=True):
    st.markdown("""
    1. **Enter your Mistral API Key** in the field below
    2. **Upload a PDF document** using the file uploader
    3. **Click 'Process Document'** to start the OCR process
    4. **View the results** and download in your preferred format
    
    **Note**: Your API key is never stored and is only used to make requests to the Mistral API.
    """)

# Separator
st.markdown("---")

# Setup section
st.subheader("Setup")

# API key input
api_key_col1, api_key_col2 = st.columns([3, 1])
with api_key_col1:
    api_key = st.text_input(
        "Enter your Mistral API Key:", 
        type="password",
        help="Your Mistral API Key is required to access the OCR service. Get one from the Mistral AI platform."
    )
with api_key_col2:
    st.markdown("<br>", unsafe_allow_html=True)  # For vertical alignment
    if api_key:
        st.success("API Key provided")
    else:
        st.warning("API Key needed")

# Separator
st.markdown("---")
st.subheader("Upload Document")

# File uploader with custom styling
uploaded_file = st.file_uploader(
    "Drag and drop a PDF file here or click to browse",
    type=["pdf"],
    help="Upload a PDF document to extract text using OCR"
)

# Display file information if uploaded
if uploaded_file:
    file_details_col1, file_details_col2 = st.columns(2)
    with file_details_col1:
        st.info(f"**Selected file:** {uploaded_file.name}")
    with file_details_col2:
        file_size_kb = round(len(uploaded_file.getvalue()) / 1024, 2)
        st.info(f"**File size:** {file_size_kb} KB")

# Initialize session state for storing results
if 'ocr_result' not in st.session_state:
    st.session_state.ocr_result = None
if 'markdown_content' not in st.session_state:
    st.session_state.markdown_content = None
if 'json_content' not in st.session_state:
    st.session_state.json_content = None

# Function to upload PDF to Mistral
def upload_pdf(file_path, client):
    with open(file_path, "rb") as file:
        uploaded_file = client.files.upload(
            file={
                "file_name": os.path.basename(file_path),
                "content": file,
            },
            purpose="ocr"
        )
    return uploaded_file

# Function to get signed URL
def get_signed_url(file_id, client):
    signed_url = client.files.get_signed_url(file_id=file_id)
    return signed_url.url

# Function to process document with OCR
def process_full_document(document_url, client):
    try:
        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": document_url,
            }
        )
        return ocr_response
    except Exception as e:
        st.error(f"Error processing document: {e}")
        return None

# Function to generate markdown content
def generate_markdown_content(ocr_data):
    markdown_text = ""
    for page in ocr_data["pages"]:
        page_number = page.get("index", "unknown")
        markdown_content = page.get("markdown", "")
        
        markdown_text += f"## Page {page_number}\n\n"
        markdown_text += markdown_content
        markdown_text += "\n\n---\n\n"
    
    return markdown_text

# Main processing function
def process_document():
    if not api_key:
        st.warning("Please enter your Mistral API Key.")
        return
    
    if not uploaded_file:
        st.warning("Please upload a PDF file.")
        return
    
    # Create Mistral client
    try:
        client = Mistral(api_key=api_key)
    except Exception as e:
        st.error(f"Failed to initialize Mistral client. Please check your API key: {str(e)}")
        return
    
    # Show processing status
    with st.status("Processing document...", expanded=True) as status:
        st.write("Saving uploaded file...")
        
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            temp_file_path = tmp_file.name
        
        try:
            # Step 1: Upload to Mistral
            st.write("📤 Uploading to Mistral...")
            try:
                uploaded_file_obj = upload_pdf(temp_file_path, client)
                st.write(f"✅ File uploaded with ID: {uploaded_file_obj.id}")
            except Exception as e:
                st.error(f"Mistral API Error during upload: {str(e)}")
                status.update(label="Upload failed", state="error")
                return
            
            # Step 2: Get signed URL
            st.write("🔗 Getting signed URL...")
            try:
                signed_url = get_signed_url(uploaded_file_obj.id, client)
                st.write("✅ Got signed URL")
            except Exception as e:
                st.error(f"Mistral API Error getting signed URL: {str(e)}")
                status.update(label="Failed to get signed URL", state="error")
                return
            
            # Step 3: Process with OCR
            st.write("🔍 Processing document with OCR...")
            try:
                ocr_result = process_full_document(signed_url, client)
                if not ocr_result:
                    status.update(label="OCR processing failed", state="error")
                    return
            except Exception as e:
                st.error(f"Mistral API Error during OCR processing: {str(e)}")
                status.update(label="OCR processing failed", state="error")
                return
            
            # Step 4: Process results
            st.write("✨ Processing OCR results...")
            try:
                # Convert to dict for easier handling
                result_data = ocr_result.model_dump()
                
                # Log some info about the pages
                page_count = len(result_data.get("pages", []))
                st.write(f"📄 Processed {page_count} pages")
                
                # Generate markdown content
                markdown_content = generate_markdown_content(result_data)
                
                # Store results in session state
                st.session_state.ocr_result = result_data
                st.session_state.markdown_content = markdown_content
                st.session_state.json_content = json.dumps(result_data, indent=2)
                
                time.sleep(0.5)  # Short delay for visual feedback
                status.update(label="✅ Processing complete!", state="complete")
            except Exception as e:
                st.error(f"Error processing results: {str(e)}")
                status.update(label="Error processing results", state="error")
        
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
            status.update(label="Error", state="error")
        
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

# Separator
st.markdown("---")

# Process button
if uploaded_file and api_key:
    st.markdown("""
    <div style="display: flex; justify-content: center; margin: 20px 0;">
    """, unsafe_allow_html=True)
    if st.button("🔍 Process Document", use_container_width=True):
        process_document()
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    if not api_key:
        st.warning("⚠️ Please enter your Mistral API Key to proceed")
    if not uploaded_file:
        st.warning("⚠️ Please upload a PDF document to proceed")
    st.markdown('</div>', unsafe_allow_html=True)

# Display results if available
if st.session_state.ocr_result:
    st.header("Results")
    
    # File information
    if uploaded_file:
        file_info_col1, file_info_col2 = st.columns(2)
        with file_info_col1:
            st.info(f"**File Name**: {uploaded_file.name}")
        with file_info_col2:
            file_size_kb = round(len(uploaded_file.getvalue()) / 1024, 2)
            st.info(f"**File Size**: {file_size_kb} KB")
    
    # Stats about the OCR result
    if st.session_state.ocr_result:
        page_count = len(st.session_state.ocr_result.get("pages", []))
        st.success(f"Successfully processed {page_count} pages")
    
    # Download buttons
    st.subheader("Download Results")
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="Download JSON",
            data=st.session_state.json_content,
            file_name=f"ocr_result_{int(time.time())}.json",
            mime="application/json",
            help="Download the full OCR result in JSON format"
        )
    
    with col2:
        st.download_button(
            label="Download Markdown",
            data=st.session_state.markdown_content,
            file_name=f"ocr_result_{int(time.time())}.md",
            mime="text/markdown",
            help="Download the extracted text in Markdown format"
        )
    
    # Preview tabs
    st.subheader("Preview")
    tab1, tab2 = st.tabs(["Extracted Text", "Raw JSON"])
    
    with tab1:
        st.markdown("""
        <style>
        .markdown-text-container {
            max-height: 500px;
            overflow-y: auto;
            padding: 10px;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            background-color: #f9f9f9;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="markdown-text-container">', unsafe_allow_html=True)
        st.markdown(st.session_state.markdown_content)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.json(st.session_state.ocr_result)