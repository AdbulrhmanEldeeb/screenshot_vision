import streamlit as st
import io
import base64
import time
from PIL import Image
from groq import Groq
import os
import subprocess
import platform
import tempfile

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from dotenv import load_dotenv 
load_dotenv() 
try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    st.error("webdriver_manager is not installed. Run: pip install webdriver-manager")

class SeleniumScreenshotVisionApp:
    def __init__(self):
        self.client = Groq(
            api_key=os.environ.get("GROQ_API_KEY", "")  # Get API key from environment
        )
        st.title("Web Screenshot Vision Processor")
        st.write("This app captures screenshots of websites and analyzes them using vision AI.")
        
        # Check for Chrome browser and display appropriate messages
        self.check_chrome_installation()
        
        self.run()
    
    def check_chrome_installation(self):
        """Check if Chrome is installed and provide guidance if not."""
        # Try to detect Chrome/Chromium location based on OS
        chrome_path = self.find_chrome_binary()
        
        if not chrome_path:
            st.warning("Chrome browser not detected. You need to install Chrome/Chromium or specify its location.")
            
            # Show installation instructions based on OS
            system = platform.system().lower()
            if "linux" in system:
                st.info("""
                **Install Chrome on Linux:**
                ```
                wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
                sudo apt install ./google-chrome-stable_current_amd64.deb
                ```
                
                **Or install Chromium:**
                ```
                sudo apt install chromium-browser
                ```
                """)
            elif "darwin" in system:  # macOS
                st.info("""
                **Install Chrome on macOS:**
                ```
                brew install --cask google-chrome
                ```
                
                Or download from: https://www.google.com/chrome/
                """)
            elif "windows" in system:
                st.info("""
                **Install Chrome on Windows:**
                Download and install from: https://www.google.com/chrome/
                """)
            
            # Option to specify Chrome binary path manually
            chrome_binary_path = st.text_input(
                "Specify Chrome/Chromium binary path (if installed in non-standard location)",
                help="Example: /usr/bin/chromium-browser or C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            )
            
            if chrome_binary_path and os.path.exists(chrome_binary_path):
                st.success(f"Using Chrome binary at: {chrome_binary_path}")
                return chrome_binary_path
                
        return chrome_path
    
    def find_chrome_binary(self):
        """Attempt to find Chrome or Chromium on the system."""
        system = platform.system().lower()
        
        # Common locations based on OS
        if "linux" in system:
            possible_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
                "/snap/bin/chromium",
            ]
        elif "darwin" in system:  # macOS
            possible_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
            ]
        elif "windows" in system:
            possible_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            ]
        else:
            return None
        
        # Check each path
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # If not found in common locations, try using 'which' command on Unix-like systems
        if "win" not in system:
            try:
                chrome_path = subprocess.check_output(["which", "google-chrome"], text=True).strip()
                if chrome_path:
                    return chrome_path
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
                
            try:
                chromium_path = subprocess.check_output(["which", "chromium-browser"], text=True).strip()
                if chromium_path:
                    return chromium_path
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
        
        return None

    def setup_webdriver(self, url, chrome_binary=None):
        """Set up and return a configured Chrome webdriver."""
        options = Options()
        # options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # Additional options to make Selenium more reliable
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        
        # Set chrome binary path if provided
        if chrome_binary and os.path.exists(chrome_binary):
            options.binary_location = chrome_binary
        
        try:
            # Use webdriver_manager if available
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except Exception as e:
            st.error(f"Error setting up Chrome driver: {str(e)}")
            st.info("Attempting alternative screenshot method...")
            
            # Fallback to a simpler method: try using Firefox if available
            try:
                from selenium.webdriver.firefox.options import Options as FirefoxOptions
                firefox_options = FirefoxOptions()
                firefox_options.add_argument("--headless")
                driver = webdriver.Firefox(options=firefox_options)
                return driver
            except Exception as firefox_error:
                st.error(f"Firefox fallback also failed: {str(firefox_error)}")
                
                # Last resort: Use a Python-based solution
                st.info("Using Python-based screenshot solution as last resort...")
                try:
                    import urllib.request
                    import html2image
                    
                    # Download the webpage HTML
                    with urllib.request.urlopen(url) as response:
                        html = response.read()
                    
                    # Save to a temporary file
                    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as temp:
                        temp.write(html)
                        temp_path = temp.name
                    
                    # Use html2image to render it
                    hti = html2image.Html2Image()
                    screenshot_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
                    hti.screenshot(html=temp_path, save_as=screenshot_path)
                    
                    # Clean up
                    os.unlink(temp_path)
                    
                    # Return a custom "driver" object with a get_screenshot_as_png method
                    class PseudoDriver:
                        def get_screenshot_as_png(self):
                            with open(screenshot_path, "rb") as f:
                                data = f.read()
                            os.unlink(screenshot_path)  # Clean up
                            return data
                        
                        def quit(self):
                            pass
                    
                    return PseudoDriver()
                    
                except Exception as last_error:
                    st.error(f"All screenshot methods failed: {str(last_error)}")
                    st.error("Please install Chrome or another browser and try again.")
                    return None

    def take_screenshot(self, url, wait_time=5, chrome_binary=None):
        """Capture a screenshot of the specified URL using Selenium."""
        try:
            driver = self.setup_webdriver(url, chrome_binary)
            if not driver:
                return None
                
            # Navigate to the URL
            driver.get(url)
            
            # Wait for the page to load
            time.sleep(wait_time)
            
            # Take the screenshot
            screenshot = driver.get_screenshot_as_png()
            
            # Clean up
            driver.quit()
            
            return screenshot
            
        except Exception as e:
            st.error(f"Error taking screenshot: {str(e)}")
            return None

    def encode_image(self, image_bytes):
        """Convert image bytes to a base64 string."""
        return base64.b64encode(image_bytes).decode("utf-8")

    def process_image(self, image_bytes, prompt):
        """Send image to the vision model for processing."""
        if not self.client.api_key:
            st.error("No GROQ API key found. Please set the GROQ_API_KEY environment variable.")
            return "No API key provided. Cannot process image."
            
        base64_image = self.encode_image(image_bytes)
        
        # Prepare message for the vision model
        message_content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
        ]

        try:
            # Process with vision model
            response = self.client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[{"role": "user", "content": message_content}],
                temperature=0.7,
                max_tokens=512,
                top_p=1.0
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"Error processing with vision model: {str(e)}")
            return f"Error: {str(e)}"

    def run(self):
        """Run the Streamlit UI."""
        with st.form("screenshot_form"):
            url = st.text_input(
                "Website URL", 
                value="https://news.ycombinator.com/",
                help="Enter the URL of the website you want to capture"
            )
            
            wait_time = st.slider(
                "Wait time (seconds)", 
                min_value=1, 
                max_value=15, 
                value=5,
                help="Time to wait for the page to load before taking the screenshot"
            )
            
            prompt = st.text_area(
                "Vision model prompt", 
                value="What's on this webpage? Summarize the main content and describe the layout.",
                help="Question to ask the vision model about the screenshot"
            )
            
            chrome_binary = self.check_chrome_installation()
            
            submitted = st.form_submit_button("Capture and Analyze")
        
        if submitted:
            with st.spinner(f"Navigating to {url} and capturing screenshot..."):
                screenshot_bytes = self.take_screenshot(url, wait_time, chrome_binary)
                
                if screenshot_bytes:
                    # Display the screenshot
                    img = Image.open(io.BytesIO(screenshot_bytes))
                    st.image(img, caption=f"Screenshot of {url}", use_column_width=True)
                    
                    # Process the image
                    with st.spinner("Analyzing screenshot with vision model..."):
                        result = self.process_image(screenshot_bytes, prompt)
                    
                    # Display results
                    st.success("Analysis complete!")
                    st.write("### Vision Model Analysis:")
                    st.write(result)
                    
                    # Option to save
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Save Screenshot"):
                            timestamp = time.strftime("%Y%m%d-%H%M%S")
                            with open(f"screenshot_{timestamp}.png", "wb") as f:
                                f.write(screenshot_bytes)
                            st.success(f"Screenshot saved as screenshot_{timestamp}.png")
                    
                    with col2:
                        if st.button("Save Analysis"):
                            timestamp = time.strftime("%Y%m%d-%H%M%S")
                            with open(f"analysis_{timestamp}.txt", "w") as f:
                                f.write(result)
                            st.success(f"Analysis saved as analysis_{timestamp}.txt")

if __name__ == "__main__":
    # Install required packages if missing
    try:
        import html2image
    except ImportError:
        st.warning("Installing required package: html2image")
        subprocess.run(["pip", "install", "html2image"])
        # st.expr()

    SeleniumScreenshotVisionApp()