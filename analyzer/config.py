import os


MODEL_PATH = os.getenv("MODEL_PATH", "data/best.pt")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "5005"))


