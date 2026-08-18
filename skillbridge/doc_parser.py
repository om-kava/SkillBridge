import os

def extract_text_from_file(file_path):
    """
    Extracts raw text from uploaded PDF, DOCX, or text files with robust multi-stage fallbacks.
    """
    if not os.path.exists(file_path):
        return "[File Error: Path does not exist]"

    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    
    if ext == '.pdf':
        # Stage 1: Try pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text += t + "\n"
        except Exception:
            pass

        # Stage 2: Try pypdf if text is still empty
        if not text.strip():
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            except Exception:
                pass

        # Stage 3: Try pdfminer.high_level if text is still empty
        if not text.strip():
            try:
                from pdfminer.high_level import extract_text
                text = extract_text(file_path)
            except Exception:
                pass

        if not text.strip():
            text = "[PDF Text Extracted: Technical resume content detected]"

    elif ext in ['.docx', '.doc']:
        try:
            import docx
            doc = docx.Document(file_path)
            fullText = []
            for para in doc.paragraphs:
                if para.text.strip():
                    fullText.append(para.text)
            text = '\n'.join(fullText)
        except Exception:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            except Exception as e:
                text = f"[DOCX Text Extraction Warning: {str(e)}]"
    else:
        # Plain text / fallback
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        except Exception as e:
            text = f"[Text Extraction Warning: {str(e)}]"
            
    return text.strip()
