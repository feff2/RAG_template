import os

from dotenv import load_dotenv

load_dotenv()

server_ip = os.getenv("EMBEDDING_SERVER_IP", "localhost")

top_k = 5
max_tokens = 2048
temperature = 0.7
model_name = "Qwen/Qwen3-4B"
embedding_model_dim = 384
embedding_server_url = f"http://{server_ip}:1235/embed"
llm_server_url = f"http://{server_ip}:1234/v1"
db_server_url = f"http://{server_ip}:6333"
llm_api_key = "dal_jazzu"
