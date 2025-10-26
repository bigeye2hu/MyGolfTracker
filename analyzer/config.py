import os


MODEL_PATH = os.getenv("MODEL_PATH", "data/1280p_yolo11x_5090_full.pt")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "5005"))


