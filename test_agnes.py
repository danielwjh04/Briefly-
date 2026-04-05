from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = ChatOpenAI(
    model="sapiens-ai/agnes-1.5-pro",
    api_key=os.getenv("ZENMUX_API_KEY"),
    base_url="https://zenmux.ai/api/v1",
)

response = client.invoke("Hello, Agnes")
print(response.content)
