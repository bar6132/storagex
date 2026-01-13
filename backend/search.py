from elasticsearch import Elasticsearch, AsyncElasticsearch
import os

ES_URL = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
es = Elasticsearch(ES_URL)

INDEX_NAME = "videos"

def create_index():
    """Create the index if it doesn't exist"""
    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(index=INDEX_NAME, body={
            "mappings": {
                "properties": {
                    "title": {"type": "text"},
                    "description": {"type": "text"},
                    "category": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "owner_id": {"type": "integer"}
                }
            }
        })
        print("✅ Elasticsearch Index Created!")

def index_video(video_id: str, title: str, description: str, category: str):
    """Save a video into the search engine"""
    doc = {
        "title": title,
        "description": description,
        "category": category,
        "id": video_id
    }
    try:
        es.index(index=INDEX_NAME, id=video_id, document=doc)
        print(f"[🔎] Indexed video {video_id}")
    except Exception as e:
        print(f"[!] ES Indexing failed: {e}")

def search_videos(query: str = None, category: str = None):
    """Search for videos with fuzzy matching"""
    must_clauses = []

    if query:
        must_clauses.append({
            "multi_match": {
                "query": query,
                "fields": ["title^3", "description"], 
                "fuzziness": "AUTO" 
            }
        })
    
    if category and category != "All":
        must_clauses.append({"term": {"category": category}})

    body = {
        "query": {
            "bool": {
                "must": must_clauses
            }
        }
    }
    
    if not must_clauses:
        body = {"query": {"match_all": {}}}

    res = es.search(index=INDEX_NAME, body=body, size=50)
    
    return [hit["_id"] for hit in res["hits"]["hits"]]