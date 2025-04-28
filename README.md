# Mistral OCR Streamlit App

A simple Streamlit application for extracting text from PDF documents using Mistral AI's OCR capabilities.

## Features

- Drag-and-drop interface for PDF uploads
- OCR processing using Mistral AI's OCR service
- View extracted text in Markdown format
- Download results as Markdown or JSON
- No API key storage - input only when needed

## Requirements

- Python 3.8+
- Streamlit
- Mistral AI Python SDK

## Installation

1. Clone this repository or download the files
2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit app:

```bash
streamlit run app.py
```

2. Open the provided URL in your web browser (typically http://localhost:8501)
3. Enter your Mistral API key
4. Upload a PDF document
5. Click "Process Document"
6. View and download the extracted text

## Important Notes

- You need a valid Mistral AI API key to use this application
- Your API key is not stored anywhere and is only used for the current session
- Processing time depends on the PDF file size and complexity

## Files

- `app.py` - The main Streamlit application
- `requirements.txt` - Required Python packages
- `README.md` - This documentation

## How It Works

The application:
1. Accepts a PDF upload from the user
2. Sends the PDF to Mistral's OCR service
3. Processes the OCR results
4. Displays the extracted text and provides download options

## Troubleshooting

If you encounter any issues:
- Make sure your Mistral API key is valid
- Ensure the PDF file is readable and not corrupted
- Check that you have a stable internet connection