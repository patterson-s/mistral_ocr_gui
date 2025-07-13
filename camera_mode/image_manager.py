import streamlit as st
import base64
from io import BytesIO
from PIL import Image
from typing import List, Optional

class ImageManager:
    def __init__(self):
        if 'captured_images' not in st.session_state:
            st.session_state.captured_images = []
    
    def add_image(self, image_data: str) -> None:
        """Add a new image to the collection"""
        st.session_state.captured_images.append({
            'data': image_data,
            'id': len(st.session_state.captured_images)
        })
    
    def remove_image(self, index: int) -> None:
        """Remove an image by index"""
        if 0 <= index < len(st.session_state.captured_images):
            st.session_state.captured_images.pop(index)
            # Update IDs
            for i, img in enumerate(st.session_state.captured_images):
                img['id'] = i
    
    def clear_all_images(self) -> None:
        """Clear all captured images"""
        st.session_state.captured_images = []
    
    def get_all_images(self) -> List[dict]:
        """Get all captured images"""
        return st.session_state.captured_images
    
    def has_images(self) -> bool:
        """Check if any images are captured"""
        return len(st.session_state.captured_images) > 0
    
    def get_image_count(self) -> int:
        """Get the number of captured images"""
        return len(st.session_state.captured_images)
    
    def reorder_images(self, old_index: int, new_index: int) -> None:
        """Reorder images (move image from old_index to new_index)"""
        if (0 <= old_index < len(st.session_state.captured_images) and 
            0 <= new_index < len(st.session_state.captured_images)):
            images = st.session_state.captured_images
            image = images.pop(old_index)
            images.insert(new_index, image)
            # Update IDs
            for i, img in enumerate(images):
                img['id'] = i
    
    def render_image_gallery(self) -> None:
        """Render the image gallery with management controls"""
        if not self.has_images():
            st.info("📷 No images captured yet. Use the camera above to start!")
            return
        
        st.markdown("---")
        st.subheader(f"Captured Images ({self.get_image_count()})")
        
        # Gallery controls
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.write(f"**{self.get_image_count()} images ready for processing**")
        
        with col2:
            if st.button("🗑️ Clear All Images"):
                self.clear_all_images()
                st.rerun()
        
        with col3:
            pass  # Reserved for future controls
        
        # Display images in a grid
        images = self.get_all_images()
        cols_per_row = 3
        
        for i in range(0, len(images), cols_per_row):
            cols = st.columns(cols_per_row)
            
            for j in range(cols_per_row):
                idx = i + j
                if idx < len(images):
                    with cols[j]:
                        self._render_image_card(images[idx], idx)
    
    def _render_image_card(self, image_data: dict, index: int) -> None:
        """Render a single image card with controls"""
        # Extract base64 data for display
        img_data = image_data['data']
        
        # Display image
        st.image(img_data, caption=f"Image {index + 1}", use_column_width=True)
        
        # Image controls
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️", key=f"delete_{index}", help="Delete this image"):
                self.remove_image(index)
                st.rerun()
        
        with col2:
            # Move controls (simplified)
            if index > 0:
                if st.button("⬆️", key=f"up_{index}", help="Move up"):
                    self.reorder_images(index, index - 1)
                    st.rerun()
    
    def convert_images_for_processing(self) -> List[BytesIO]:
        """Convert captured images to format suitable for OCR processing"""
        processed_images = []
        
        for img_data in self.get_all_images():
            try:
                # Extract base64 data
                img_str = img_data['data']
                if img_str.startswith('data:image'):
                    img_str = img_str.split(',')[1]
                
                # Decode base64 to bytes
                img_bytes = base64.b64decode(img_str)
                
                # Convert to PIL Image for processing
                img = Image.open(BytesIO(img_bytes))
                
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save to BytesIO object
                processed_img = BytesIO()
                img.save(processed_img, format='JPEG', quality=90)
                processed_img.seek(0)
                
                processed_images.append(processed_img)
                
            except Exception as e:
                st.error(f"Error processing image: {str(e)}")
                continue
        
        return processed_images