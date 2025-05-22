#!/usr/bin/env python3
"""
Batch OCR processor using Mistral AI
Processes all PDF, JPEG, and PNG files in a folder using Mistral's OCR service
"""

import os
import json
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from mistralai import Mistral
from typing import List, Dict, Any


class BatchOCRProcessor:
    def __init__(self, api_key: str):
        """Initialize the OCR processor with Mistral API key"""
        self.client = Mistral(api_key=api_key)
        self.supported_extensions = {'.pdf', '.jpg', '.jpeg', '.png'}
    
    def find_documents(self, input_folder: str) -> List[Path]:
        """Find all supported document files in the input folder"""
        input_path = Path(input_folder)
        if not input_path.exists():
            raise FileNotFoundError(f"Input folder does not exist: {input_folder}")
        
        documents = []
        for file_path in input_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                documents.append(file_path)
        
        return sorted(documents)
    
    def upload_document(self, file_path: Path) -> str:
        """Upload document to Mistral and return file ID"""
        print(f"  📤 Uploading {file_path.name}...")
        
        with open(file_path, "rb") as file:
            uploaded_file = self.client.files.upload(
                file={
                    "file_name": file_path.name,
                    "content": file,
                },
                purpose="ocr"
            )
        return uploaded_file.id
    
    def get_signed_url(self, file_id: str) -> str:
        """Get signed URL for the uploaded file"""
        signed_url = self.client.files.get_signed_url(file_id=file_id)
        return signed_url.url
    
    def process_document(self, document_url: str, file_extension: str) -> Dict[Any, Any]:
        """Process document with OCR using appropriate document type"""
        print(f"  🔍 Processing with OCR...")
        
        # Determine document type based on file extension
        image_extensions = {'.jpg', '.jpeg', '.png'}
        
        if file_extension.lower() in image_extensions:
            document_config = {
                "type": "image_url",
                "image_url": document_url,
            }
        else:  # PDF and other documents
            document_config = {
                "type": "document_url",
                "document_url": document_url,
            }
        
        ocr_response = self.client.ocr.process(
            model="mistral-ocr-latest",
            document=document_config
        )
        return ocr_response.model_dump()
    
    def generate_markdown_content(self, ocr_data: Dict[Any, Any]) -> str:
        """Generate markdown content from OCR data"""
        markdown_text = ""
        for page in ocr_data.get("pages", []):
            page_number = page.get("index", "unknown")
            markdown_content = page.get("markdown", "")
            
            markdown_text += f"## Page {page_number}\n\n"
            markdown_text += markdown_content
            markdown_text += "\n\n---\n\n"
        
        return markdown_text
    
    def save_results(self, output_folder: Path, file_name: str, ocr_data: Dict[Any, Any], 
                    markdown_content: str) -> Dict[str, Any]:
        """Return document result for batch compilation"""
        return {
            "document_name": file_name,
            "markdown_content": markdown_content,
            "raw_ocr_data": ocr_data
        }
    
    def process_single_file(self, file_path: Path, output_folder: Path) -> Dict[str, Any]:
        """Process a single document file and return result data"""
        try:
            print(f"\n📄 Processing: {file_path.name}")
            
            # Upload document
            file_id = self.upload_document(file_path)
            
            # Get signed URL
            signed_url = self.get_signed_url(file_id)
            
            # Process with OCR (pass file extension for proper document type)
            ocr_data = self.process_document(signed_url, file_path.suffix)
            
            # Generate markdown
            markdown_content = self.generate_markdown_content(ocr_data)
            
            # Prepare result data
            result = self.save_results(output_folder, file_path.name, ocr_data, markdown_content)
            
            # Log stats
            page_count = len(ocr_data.get("pages", []))
            print(f"  📊 Processed {page_count} pages")
            print(f"  ✅ Added to batch results")
            
            return result
            
        except Exception as e:
            print(f"  ❌ Error processing {file_path.name}: {str(e)}")
            return None
    
    def process_batch(self, input_folder: str, output_folder: str) -> None:
        """Process all documents in the input folder"""
        # Setup output folder
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find documents
        documents = self.find_documents(input_folder)
        
        if not documents:
            print(f"No supported documents found in {input_folder}")
            print(f"Supported formats: {', '.join(self.supported_extensions)}")
            return
        
        print(f"Found {len(documents)} documents to process")
        print(f"Output folder: {output_path.absolute()}")
        
        # Process each document
        all_results = []
        successful = 0
        failed = 0
        
        for i, doc_path in enumerate(documents, 1):
            print(f"\n{'='*60}")
            print(f"Processing {i}/{len(documents)}")
            
            result = self.process_single_file(doc_path, output_path)
            if result:
                all_results.append(result)
                successful += 1
            else:
                failed += 1
            
            # Add a small delay between requests to be respectful to the API
            if i < len(documents):
                time.sleep(1)
        
        # Save all results to a single JSON file
        if all_results:
            timestamp = int(time.time())
            output_file = output_path / f"batch_ocr_results_{timestamp}.json"
            
            batch_data = {
                "processing_summary": {
                    "total_documents": len(documents),
                    "successful": successful,
                    "failed": failed,
                    "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "input_folder": str(input_folder),
                    "output_folder": str(output_folder)
                },
                "documents": all_results
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(batch_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 All results saved to: {output_file.name}")
        
        # Final summary
        print(f"\n{'='*60}")
        print(f"🎉 Batch processing complete!")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📁 Results saved to: {output_path.absolute()}")


def validate_api_key(api_key: str) -> bool:
    """Validate API key by making a simple test call"""
    try:
        print("🔍 Validating API key...")
        client = Mistral(api_key=api_key)
        
        # Make a simple chat completion call to test the API key
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        
        print("✅ API key is valid!")
        return True
        
    except Exception as e:
        error_message = str(e).lower()
        
        if "401" in error_message or "unauthorized" in error_message:
            print("❌ API key validation failed: Invalid or expired API key")
        elif "403" in error_message or "forbidden" in error_message:
            print("❌ API key validation failed: Access denied or insufficient permissions")
        elif "quota" in error_message or "limit" in error_message:
            print("❌ API key validation failed: Quota exceeded or rate limit reached")
        elif "credits" in error_message or "billing" in error_message:
            print("❌ API key validation failed: Insufficient credits or billing issue")
        else:
            print(f"❌ API key validation failed: {str(e)}")
        
        print("\n💡 Troubleshooting tips:")
        print("   • Check your API key at: https://console.mistral.ai/")
        print("   • Verify your account has available credits")
        print("   • Make sure your key hasn't expired")
        print("   • Try generating a new API key")
        
        return False


def get_api_key() -> str:
    """Prompt user for API key and validate it"""
    print("🔑 Mistral API Key Required")
    print("You can get your API key from: https://console.mistral.ai/")
    
    max_attempts = 3
    for attempt in range(max_attempts):
        if attempt > 0:
            print(f"\nAttempt {attempt + 1}/{max_attempts}")
        
        api_key = input("\nEnter your Mistral API Key: ").strip()
        if not api_key:
            print("❌ API key cannot be empty")
            continue
        
        # Validate the API key
        if validate_api_key(api_key):
            return api_key
        
        if attempt < max_attempts - 1:
            retry = input("\nWould you like to try a different API key? (y/N): ").strip().lower()
            if retry not in ['y', 'yes']:
                break
    
    raise ValueError("Failed to validate API key after multiple attempts")


def select_folder(title: str, initial_dir: str = None) -> str:
    """Open a GUI folder selection dialog"""
    # Create a root window and hide it
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)  # Bring dialog to front
    
    # Open folder selection dialog
    folder_path = filedialog.askdirectory(
        title=title,
        initialdir=initial_dir
    )
    
    root.destroy()
    return folder_path


def main():
    print("🚀 Mistral Batch OCR Processor")
    print("=" * 50)
    
    try:
        # Get API key
        api_key = get_api_key()
        print("✅ API key provided")
        
        # Get input folder
        print("\n📁 Select Input Folder")
        print("Please select the folder containing your documents...")
        input_folder = select_folder("Select Input Folder (documents to process)")
        
        if not input_folder:
            print("❌ No input folder selected. Exiting.")
            return 1
        
        print(f"✅ Input folder: {input_folder}")
        
        # Get output folder
        print("\n📤 Select Output Folder")
        print("Please select where to save the OCR results...")
        
        # Suggest a default output folder next to input
        default_output = os.path.join(os.path.dirname(input_folder), "ocr_results")
        
        output_folder = select_folder(
            "Select Output Folder (where to save results)",
            initial_dir=os.path.dirname(input_folder)
        )
        
        if not output_folder:
            print("❌ No output folder selected. Exiting.")
            return 1
        
        print(f"✅ Output folder: {output_folder}")
        
        # Confirm before processing
        print(f"\n📋 Processing Summary:")
        print(f"   Input:  {input_folder}")
        print(f"   Output: {output_folder}")
        
        confirm = input("\nStart processing? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("❌ Processing cancelled.")
            return 1
        
        # Initialize processor and run
        processor = BatchOCRProcessor(api_key)
        processor.process_batch(input_folder, output_folder)
        
        # Success message
        print(f"\n🎉 All done! Check your results in: {output_folder}")
        input("\nPress Enter to exit...")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        input("\nPress Enter to exit...")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())