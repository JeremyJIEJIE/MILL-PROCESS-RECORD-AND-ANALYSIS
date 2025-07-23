import subprocess
import sys
import os
import socket
import logging
import time
import webbrowser
import threading

if hasattr(sys, '_MEIPASS'):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def open_browser_once(url):
    try:
        # 只尝试一次打开浏览器，失败不再重试
        webbrowser.open(url)
        logging.info(f"Attempted to open browser at {url}")
    except Exception as e:
        logging.error(f"Failed to open browser: {e}")

def main():
    logging.info("Starting run_app.py execution...")

    streamlit_app_script = os.path.join(base_path, "app.py")
    if not os.path.exists(streamlit_app_script):
        logging.critical(f"Streamlit app script not found at: {streamlit_app_script}")
        sys.exit(1)

    port = find_free_port()
    url = f"http://localhost:{port}"
    logging.info(f"Using port: {port}")

    command = [
        sys.executable, "-m", "streamlit", "run", streamlit_app_script,
        "--server.port", str(port),
        "--server.headless", "true"
    ]

    logging.info(f"Running Streamlit command: {' '.join(command)}")

    # 启动Streamlit进程
    process = subprocess.Popen(command)

    # 用线程异步打开浏览器，防止阻塞主线程
    threading.Thread(target=open_browser_once, args=(url,), daemon=True).start()

    try:
        # 等待子进程退出，期间可用 Ctrl+C 中断
        process.wait()
    except KeyboardInterrupt:
        logging.info("User interrupted, terminating Streamlit process.")
        process.terminate()
        process.wait()

    logging.info("Streamlit process exited, run_app.py terminating.")

if __name__ == "__main__":
    main()
