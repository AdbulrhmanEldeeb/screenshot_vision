import streamlit as st
import pyautogui
import io
from PIL import Image
from groq import Groq

class ScreenshotApp:
    def __init__(self):
        self.client = Groq()
        st.title("Screenshot AI Processor")
        self.run()
    
    def take_screenshot(self):
        screenshot = pyautogui.screenshot()
        img_byte_array = io.BytesIO()
        screenshot.save(img_byte_array, format='PNG')
        return img_byte_array.getvalue()
    
    def process_image(self, image_bytes):
        response = self.client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {"role": "system", "content": "Describe the content of this image."},
                {"role": "user", "content": image_bytes}
            ],
            temperature=0.7,
            max_tokens=512,
            top_p=1.0
        )
        return response.choices[0].message.content
    
    def run(self):
        if st.button("Take Screenshot"):
            st.write("Capturing Screenshot...")
            image_bytes = self.take_screenshot()
            st.image(Image.open(io.BytesIO(image_bytes)), caption="Captured Screenshot")
            st.write("Processing Screenshot...")
            result = self.process_image(image_bytes)
            st.write("Model Response:")
            st.write(result)

if __name__ == "__main__":
    ScreenshotApp()
