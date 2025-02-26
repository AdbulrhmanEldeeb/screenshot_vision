## to solve pyautogui schreenshot issue 
1.Install Xvfb:
sudo apt-get update
sudo apt-get install xvfb

## to solve proxies issue 
Uninstall the current version of httpx:
pip uninstall httpx
Install the compatible version of httpx:
pip install httpx==0.27.2

run command 
xvfb-run -a streamlit run main.py

install chrome 
sudo apt update
sudo apt install -y chromium-chromedriver

install google chrome 