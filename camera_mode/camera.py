import streamlit as st
from ui_components import setup_page_config, render_custom_css, render_header
from camera_component import render_camera_interface

def main():
    setup_page_config()
    render_custom_css()
    render_header()
    
    st.markdown("---")
    
    # Check for API key in environment first
    import os
    api_key = os.getenv('MISTRAL_API_KEY')
    
    if api_key:
        st.success("✅ API key found in environment variables!")
    else:
        # Ask for API key if not in environment
        st.warning("⚠️ MISTRAL_API_KEY not found in environment variables.")
        api_key = st.text_input(
            "🔑 Enter Mistral API Key",
            type="password",
            help="Enter your Mistral API key to enable OCR processing"
        )
        
        if api_key:
            os.environ['MISTRAL_API_KEY'] = api_key
            st.success("✅ API key configured for this session!")
        else:
            st.info("💡 You can get your API key from the Mistral AI platform.")
            st.stop()
    
    st.markdown("---")
    
    # Camera interface with immediate OCR processing
    render_camera_interface()

if __name__ == "__main__":
    main()