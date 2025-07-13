import streamlit as st
import json
import tempfile
import time
import os
from mistralai import Mistral
from typing import List, Optional
from utils import create_temp_file, cleanup_temp_files

class OCRProcessor:
    def __init__(self):
        self.client: Optional[Mistral] = None
        self.api_key: Optional[str] = None
        
        # Initialize session state for results
        if 'ocr_result' not in st.session_state:
            st.session_state.ocr_result = None
        if 'markdown_content' not in st.session_state:
            st.session_state.markdown_content = None
        if 'json_content' not in st.session_state:
            st.session_state.json_content = None
    
    def set_api_key(self, api_key: str) -> None:
        """Set the Mistral API key and initialize client"""
        self.api_key = api_key
        try:
            self.client = Mistral(api_key=api_key)
        except Exception as e:
            st.error(f"Failed to initialize Mistral client: {str(e)}")
            self.client = None
    
    def upload_image_to_mistral(self, image_data, filename: str):
        """Upload a single image to Mistral"""
        if not self.client:
            raise Exception("Mistral client not initialized")
        
        # Create temporary file
        temp_path = create_temp_file(image_data, filename)
        
        try:
            with open(temp_path, "rb") as file:
                uploaded_file = self.client.files.upload(
                    file={
                        "file_name": filename,
                        "content": file,
                    },
                    purpose="ocr"
                )
            return uploaded_file
        finally:
            cleanup_temp_files([temp_path])
    
    def get_signed_url(self, file_id: str) -> str:
        """Get signed URL for uploaded file"""
        if not self.client:
            raise Exception("Mistral client not initialized")
        
        signed_url = self.client.files.get_signed_url(file_id=file_id)
        return signed_url.url
    
    def process_single_image_ocr(self, document_url: str):
        """Process a single image with OCR"""
        if not self.client:
            raise Exception("Mistral client not initialized")
        
        try:
            ocr_response = self.client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": document_url,
                }
            )
            return ocr_response
        except Exception as e:
            st.error(f"Error processing image with OCR: {e}")
            return None
    
    def combine_ocr_results(self, results: List[dict]) -> dict:
        """Combine multiple OCR results into a single document"""
        combined_result = {
            "pages": [],
            "document_info": {
                "total_pages": len(results),
                "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source": "camera_capture"
            }
        }
        
        page_index = 0
        for result in results:
            if result and "pages" in result:
                for page in result["pages"]:
                    # Update page index for combined document
                    page["index"] = page_index
                    combined_result["pages"].append(page)
                    page_index += 1
        
        return combined_result
    
    def generate_markdown_content(self, ocr_data: dict) -> str:
        """Generate markdown content from OCR data"""
        markdown_text = ""
        
        # Add document header
        total_pages = len(ocr_data.get("pages", []))
        markdown_text += f"# Camera OCR Document\n\n"
        markdown_text += f"**Total Pages:** {total_pages}\n"
        markdown_text += f"**Processed:** {ocr_data.get('document_info', {}).get('processed_at', 'Unknown')}\n\n"
        markdown_text += "---\n\n"
        
        # Add content from each page
        for page in ocr_data.get("pages", []):
            page_number = page.get("index", 0) + 1
            markdown_content = page.get("markdown", "")
            
            markdown_text += f"## Page {page_number}\n\n"
            markdown_text += markdown_content
            markdown_text += "\n\n---\n\n"
        
        return markdown_text
    
    def process_images(self, images: List[dict]) -> None:
        """Process all captured images with OCR"""
        if not self.client:
            st.error("Mistral client not initialized. Please check your API key.")
            return
        
        if not images:
            st.warning("No images to process.")
            return
        
        # Convert images for processing
        image_manager = st.session_state.image_manager
        processed_images = image_manager.convert_images_for_processing()
        
        if not processed_images:
            st.error("Failed to prepare images for processing.")
            return
        
        # Show processing status
        with st.status("Processing images...", expanded=True) as status:
            ocr_results = []
            
            for i, image_data in enumerate(processed_images):
                try:
                    st.write(f"📤 Uploading image {i + 1}/{len(processed_images)}...")
                    
                    # Upload image to Mistral
                    filename = f"camera_image_{i + 1}.jpg"
                    uploaded_file = self.upload_image_to_mistral(image_data, filename)
                    st.write(f"✅ Image {i + 1} uploaded with ID: {uploaded_file.id}")
                    
                    # Get signed URL
                    st.write(f"🔗 Getting signed URL for image {i + 1}...")
                    signed_url = self.get_signed_url(uploaded_file.id)
                    
                    # Process with OCR
                    st.write(f"🔍 Processing image {i + 1} with OCR...")
                    ocr_result = self.process_single_image_ocr(signed_url)
                    
                    if ocr_result:
                        result_data = ocr_result.model_dump()
                        ocr_results.append(result_data)
                        st.write(f"✅ Image {i + 1} processed successfully")
                    else:
                        st.write(f"❌ Failed to process image {i + 1}")
                
                except Exception as e:
                    st.error(f"Error processing image {i + 1}: {str(e)}")
                    continue
            
            if ocr_results:
                st.write("✨ Combining results...")
                
                # Combine all results
                combined_result = self.combine_ocr_results(ocr_results)
                
                # Generate markdown content
                markdown_content = self.generate_markdown_content(combined_result)
                
                # Store results in session state
                st.session_state.ocr_result = combined_result
                st.session_state.markdown_content = markdown_content
                st.session_state.json_content = json.dumps(combined_result, indent=2)
                
                total_processed = len(ocr_results)
                status.update(label=f"✅ Successfully processed {total_processed} images!", state="complete")
            else:
                status.update(label="❌ No images were processed successfully", state="error")
    
    def render_results(self) -> None:
        """Render the OCR results section"""
        if not st.session_state.ocr_result:
            return
        
        st.markdown("---")
        st.header("📄 OCR Results")
        
        # Results summary
        result_data = st.session_state.ocr_result
        total_pages = len(result_data.get("pages", []))
        processed_at = result_data.get("document_info", {}).get("processed_at", "Unknown")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Total Pages Processed:** {total_pages}")
        with col2:
            st.info(f"**Processed At:** {processed_at}")
        
        # Download buttons
        st.subheader("📥 Download Results")
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="Download JSON",
                data=st.session_state.json_content,
                file_name=f"camera_ocr_result_{int(time.time())}.json",
                mime="application/json",
                help="Download the full OCR result in JSON format"
            )
        
        with col2:
            st.download_button(
                label="Download Markdown",
                data=st.session_state.markdown_content,
                file_name=f"camera_ocr_result_{int(time.time())}.md",
                mime="text/markdown",
                help="Download the extracted text in Markdown format"
            )
        
        # Preview tabs
        st.subheader("👀 Preview")
        tab1, tab2 = st.tabs(["Extracted Text", "Raw JSON"])
        
        with tab1:
            st.markdown("""
            <div style="max-height: 500px; overflow-y: auto; padding: 10px; 
                        border: 1px solid #e0e0e0; border-radius: 5px; 
                        background-color: #f9f9f9;">
            """, unsafe_allow_html=True)
            st.markdown(st.session_state.markdown_content)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tab2:
            st.json(st.session_state.ocr_result)