import subprocess
import os
import shutil

def convert_docx_to_pdf(docx_path: str) -> str:
    """Convert a docx file to PDF using LibreOffice, return PDF path"""
    output_dir = "/tmp"
    
    result = subprocess.run(
        ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", output_dir, docx_path],
        capture_output=True, text=True, timeout=30
    )
    
    if result.returncode != 0:
        raise Exception(f"PDF conversion failed: {result.stderr}")
    
    # LibreOffice outputs same filename with .pdf extension
    base = os.path.splitext(os.path.basename(docx_path))[0]
    pdf_path = os.path.join(output_dir, base + ".pdf")
    
    if not os.path.exists(pdf_path):
        raise Exception(f"PDF not found at {pdf_path}")
    
    return pdf_path
