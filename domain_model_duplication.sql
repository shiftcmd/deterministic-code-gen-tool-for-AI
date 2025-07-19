# Example: Search for domain model duplication in Inventory_scrape
import os
from dotenv import load_dotenv
import openai
from supabase import create_client

# Load environment variables
load_dotenv()

# Initialize clients
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase_client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

# Create embedding for your query
def get_embedding(text):
    response = openai_client.embeddings.create(
        model=os.getenv("MODEL_CHOICE", "text-embedding-3-large"),
        input=text,
        encoding_format="float"
    )
    return response.data[0].embedding

# Example: Search for domain model duplicates
query = "User entity with authentication attributes"
embedding = get_embedding(query)

# Execute search
results = supabase_client.rpc(
    "match_code_chunks",
    {
        "query_embedding": embedding,
        "match_threshold": 0.7,
        "match_count": 20,
        "filter_project": "Inventory_scrape",
        "filter_layer": "Domain"  # Focus on domain layer
    }
).execute()

# Process results
for item in results.data:
    print(f"Found: {item['name']} ({item['similarity']:.2f})")
    print(f"Location: {item['relative_path']}/{item['file_name']}")
    print("---")
