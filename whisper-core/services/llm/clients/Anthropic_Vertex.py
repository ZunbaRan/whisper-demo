import httpx
from anthropic import AnthropicVertex
from google.oauth2 import service_account

project_id = "gen-lang-client-0089900393"
# Where the model is running
region = "us-east5"
# region = "global"

proxies = "http://127.0.0.1:7890"
http_client = httpx.Client(proxy=proxies)

credentials_path = "vertex_credentials/gen-lang-client-0089900393-9eb47c5f818f.json"
scopes = [
    "https://www.googleapis.com/auth/cloud-platform",  # Often required for general GCP access
    "https://www.googleapis.com/auth/generative-language", # specifically for generative AI
    # Add any other specific scopes required by Anthropic Vertex AI
]
credentials = service_account.Credentials.from_service_account_file(credentials_path, scopes=scopes)

client = AnthropicVertex(project_id=project_id, region=region,
                         credentials=credentials,
                         http_client=http_client)


message = client.messages.create(
    model="claude-3-5-sonnet-v2@20241022",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "Hey Claude!",
        }
    ],
)

print(message.model_dump_json(indent=2))