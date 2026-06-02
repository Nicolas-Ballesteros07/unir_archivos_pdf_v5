from django.apps import AppConfig
import os
import threading
import time
import requests


class UnificararchivospdfConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'UnificarArchivosPdf'

    def ready(self):
        is_render = os.environ.get("RENDER") == "true"
        is_main_thread = os.environ.get("RUN_MAIN") == "true"

        if is_render or is_main_thread:
            threading.Thread(
                target=self.ejecutar_auto_ping,
                daemon=True
            ).start()

    def ejecutar_auto_ping(self):
        time.sleep(15)

        url_base = os.environ.get(
            "RENDER_EXTERNAL_URL",
            "https://unir-archivos-pdf-v5.onrender.com"
        )

        endpoint = f"{url_base.rstrip('/')}/health/"

        while True:
            try:
                response = requests.get(endpoint, timeout=15)
                print(
                    f"[Auto-Ping] {response.status_code}"
                )
            except Exception as e:
                print(f"[Auto-Ping] Error: {e}")

            time.sleep(600)