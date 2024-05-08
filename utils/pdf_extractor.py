class PDFExtractor:
    def extract_text(self, file_stream):
        reader = PyPDF2.PdfReader(file_stream)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
        return text
