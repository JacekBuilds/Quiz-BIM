import os
import subprocess

if __name__ == "__main__":
    # Ścieżka do głównego pliku Streamlit
    app_path = os.path.join(os.path.dirname(__file__), "src", "app.py")

    # Uruchomienie Streamlit jako podprocesu
    subprocess.run(["streamlit", "run", app_path])
