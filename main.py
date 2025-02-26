import streamlit as st
import mss
import io
import base64
from PIL import Image
from groq import Groq
from pyvirtualdisplay import Display

class ScreenshotApp:
    def __init__(self):
        self.client = Groq()
        st.title("Screenshot AI Processor")
        self.run()

    def take_screenshot(self):
        """Capture a screenshot using `mss` and return it as bytes."""
        with mss.mss() as sct:
            screenshot = sct.grab(sct.monitors[1])  # Captures the main screen
            img = Image.frombytes('RGB', (screenshot.width, screenshot.height), screenshot.rgb)
            img_byte_array = io.BytesIO()
            img.save(img_byte_array, format='PNG')
            return img_byte_array.getvalue()

    def encode_image(self, image_bytes):
        """Convert image bytes to a base64 string."""
        return base64.b64encode(image_bytes).decode("utf-8")

    def process_image(self, image_bytes):
        """Send image to the Groq vision model for processing."""
        base64_image = self.encode_image(image_bytes)
        
        message_content = [
            {"type": "text", "text": "Describe the content of this image."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
        ]

        response = self.client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[{"role": "user", "content": message_content}],
            temperature=0.7,
            max_tokens=512,
            top_p=1.0
        )

        return response.choices[0].message.content

    def run(self):
        """Run the Streamlit UI."""
        if st.button("Take Screenshot"):
            st.write("Capturing Screenshot...")
            image_bytes = self.take_screenshot()
            st.image(Image.open(io.BytesIO(image_bytes)), caption="Captured Screenshot")

            st.write("Processing Screenshot...")
            result = self.process_image(image_bytes)

            st.write("### Model Response:")
            st.write(result)

if __name__ == "__main__":
    # Start virtual display
    display = Display(visible=0, size=(1024, 768))
    display.start()

    try:
        ScreenshotApp()
    finally:
        display.stop()