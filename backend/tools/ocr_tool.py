import easyocr
from backend.utils.ocr_store import ocr_cache

class OCRTool:
    name = "OCRDocument"

    def __init__(self):
        self.ocr_data = ""

    def load_document(self, image_path: str):
        reader = easyocr.Reader(['en'])
        result = reader.readtext(image_path, detail=0)
        self.ocr_data = " ".join(result)
        print(f"[OCR Data Loaded]: {self.ocr_data}")

    def invoke(self, input_text: str) -> str:
        if input_text in ocr_cache:
            return ocr_cache[input_text]
        return self.ocr_data if self.ocr_data else "No OCR data loaded."