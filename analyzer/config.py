import os


MODEL_PATH = os.getenv("MODEL_PATH", "/data/ClubDetection_1000P_50R.pt")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "5005"))


