import os 
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


load_dotenv()

class Settings(BaseSettings):
    UPSCAYLE_API_KEY: str = os.getenv("UPSCAYLE_API_KEY")
    UPSCAYLE_API_URL: str = os.getenv("UPSCAYLE_API_URL")


settings = Settings()    