import streamlit as st
import tempfile
import os
import time
from mistralai import Mistral
from PIL import Image

def render_camera_interface():
    st.markdown("### 📸 Camera Capture & OCR")
    
    # Initialize session state
    if 'accumulated_text' not in st.session_state:
        st.session_state.accumulated_text = ""
    if 'last_error' not in st.session_state:
        st.session_state.last_error = None
    if 'image_count' not in st.session_state:
        st.session_state.image_count = 0
    
    # Simple camera input
    st.markdown("**Point your camera at the document and take a photo:**")
    captured_image = st.camera_input("📷 Take a photo")
    
    # Process immediately when image is captured
    if captured_image is not None:
        # Show processing status
        with st.spinner("🔍 Processing with Mistral OCR..."):
            success = process_captured_image(captured_image)
            
        if success:
            st.success(f"✅ Image {st.session_state.image_count} processed successfully!")

        else:
            st.error(f"❌ {st.session_state.last_error}")
            if st.button("🔄 Try Again", key="retry_button"):
                st.session_state.last_error = None
                st.rerun()
    
    # Display accumulated results
    render_ocr_results()

def process_captured_image(image_file) -> bool:
    """Process a captured image with Mistral OCR and accumulate text"""
    try:
        # Get API key
        api_key = os.getenv('MISTRAL_API_KEY')
        if not api_key:
            st.session_state.last_error = "Mistral API key not found. Please set MISTRAL_API_KEY environment variable."
            return False
        
        # Convert uploaded file to PIL Image
        image = Image.open(image_file)
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Increment image count
        st.session_state.image_count += 1
        current_count = st.session_state.image_count
        
        # Create temporary file for Mistral
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            image.save(tmp_file.name, 'JPEG', quality=90)
            temp_path = tmp_file.name
        
        try:
            # Initialize Mistral client
            client = Mistral(api_key=api_key)
            
            # Upload to Mistral
            with open(temp_path, "rb") as file:
                uploaded_mistral_file = client.files.upload(
                    file={
                        "file_name": f"camera_image_{current_count}.jpg",
                        "content": file,
                    },
                    purpose="ocr"
                )
            
            # Get signed URL
            signed_url_response = client.files.get_signed_url(file_id=uploaded_mistral_file.id)
            signed_url = signed_url_response.url
            
            # Process with OCR
            ocr_response = client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": signed_url,
                }
            )
            
            # Extract markdown content
            result_data = ocr_response.model_dump()
            markdown_text = ""
            
            for page in result_data.get("pages", []):
                page_number = page.get("index", 0) + 1
                markdown_content = page.get("markdown", "")
                
                if markdown_content.strip():
                    markdown_text += markdown_content.strip()
            
            if markdown_text:
                # Add to accumulated text
                if st.session_state.accumulated_text:
                    st.session_state.accumulated_text += f"\n\n--- Image {current_count} ---\n\n"
                else:
                    st.session_state.accumulated_text += f"--- Image {current_count} ---\n\n"
                
                st.session_state.accumulated_text += markdown_text
                st.session_state.last_error = None
                return True
            else:
                st.session_state.last_error = f"No text found in image {current_count}. Please try again with a clearer image."
                st.session_state.image_count -= 1  # Don't count failed attempts
                return False
                
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        st.session_state.last_error = f"Error processing image: {str(e)}"
        if 'image_count' in st.session_state:
            st.session_state.image_count -= 1  # Don't count failed attempts
        return False

def render_ocr_results():
    """Render the accumulated OCR results and controls"""
    st.markdown("---")
    
    # Display accumulated text
    if st.session_state.accumulated_text:
        st.subheader(f"📄 Extracted Text ({st.session_state.image_count} images)")
        
        # Controls
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write("**Accumulated OCR Results:**")
        with col2:
            if st.button("🗑️ Clear All", key="clear_all"):
                st.session_state.accumulated_text = ""
                st.session_state.image_count = 0
                st.session_state.last_error = None
                st.rerun()
        with col3:
            st.download_button(
                label="📥 Download",
                data=st.session_state.accumulated_text,
                file_name=f"camera_ocr_{int(time.time())}.md",
                mime="text/markdown",
                key="download_button"
            )
        
        # Text area with accumulated results (editable)
        edited_text = st.text_area(
            "OCR Results:",
            value=st.session_state.accumulated_text,
            height=400,
            help="Text extracted from all captured images - you can edit this text",
            key="accumulated_text_display"
        )
        
        # Update session state if text was edited
        if edited_text != st.session_state.accumulated_text:
            st.session_state.accumulated_text = edited_text
        
        # Instructions for next steps
        st.info("📸 Take another photo above to add more text, or download your results!")
        
    else:
        st.info("📷 Take your first photo above to see OCR results here!")
        
        # Show helpful tips
        with st.expander("💡 Tips for better OCR results"):
            st.markdown("""
            - **Good lighting**: Make sure your document is well-lit
            - **Steady hands**: Hold the camera steady when taking the photo
            - **Full page**: Try to capture the entire page or section
            - **Straight angle**: Keep the camera parallel to the document
            - **Clear text**: Ensure text is in focus and not blurry
            - **High contrast**: Dark text on light background works best
            """)