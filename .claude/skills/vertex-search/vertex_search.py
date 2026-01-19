#!/usr/bin/env python3
"""
Vertex AI RAG Search Skill
Searches knowledge from BigQuery embeddings and GCS metadata
"""
import sys
import json
import yaml
from pathlib import Path
from typing import List, Dict, Any
from google.cloud import bigquery, storage
import vertexai
from vertexai.language_models import TextEmbeddingModel

# Load config
config_path = Path(__file__).parent.parent.parent.parent / "config" / "vertex_config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)

PROJECT_ID = config['project_id']
LOCATION = config['location']
SIMILARITY_THRESHOLD = config['search']['similarity_threshold']
MAX_RESULTS = config['search']['max_results']


def get_query_embedding(query: str) -> List[float]:
    """Generate embedding for search query"""
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = TextEmbeddingModel.from_pretrained(config['embedding']['model'])
    embeddings = model.get_embeddings([query])
    return embeddings[0].values


def search_bigquery(query_embedding: List[float], bq_client: bigquery.Client) -> List[Dict[str, Any]]:
    """Search BigQuery for similar embeddings"""
    # Convert embedding to string format for SQL
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

    query = f"""
    WITH query_embedding AS (
        SELECT {embedding_str} as embedding
    )
    SELECT
        content,
        metadata,
        created_at,
        ML.DISTANCE(embedding, query_embedding.embedding, 'COSINE') as distance
    FROM
        `{PROJECT_ID}.{config['bigquery']['knowledge_dataset']}.{config['bigquery']['knowledge_table']}`,
        query_embedding
    WHERE
        ML.DISTANCE(embedding, query_embedding.embedding, 'COSINE') < {1 - SIMILARITY_THRESHOLD}
    ORDER BY
        distance ASC
    LIMIT {MAX_RESULTS}
    """

    try:
        results = []
        query_job = bq_client.query(query)
        for row in query_job:
            results.append({
                'content': row.content,
                'metadata': json.loads(row.metadata) if isinstance(row.metadata, str) else row.metadata,
                'created_at': row.created_at.isoformat() if row.created_at else None,
                'relevance': 1 - row.distance,
                'source': 'BigQuery'
            })
        return results
    except Exception as e:
        print(f"BigQuery search error: {e}", file=sys.stderr)
        return []


def search_gcs(query: str, gcs_client: storage.Client) -> List[Dict[str, Any]]:
    """Search GCS metadata for relevant files"""
    bucket_name = config['gcs']['bucket']
    bucket = gcs_client.bucket(bucket_name)

    results = []
    query_lower = query.lower()

    # Search in decisions folder
    for blob in bucket.list_blobs(prefix=config['gcs']['folders']['decisions']):
        if blob.name.endswith('/'):
            continue

        # Check metadata
        metadata = blob.metadata or {}
        content_preview = ""

        # Download small files for keyword matching
        if blob.size < 100000:  # Only download files < 100KB
            try:
                content = blob.download_as_text()
                if query_lower in content.lower():
                    content_preview = content[:500]
                    results.append({
                        'content': content_preview,
                        'metadata': {
                            'filename': blob.name,
                            'size': blob.size,
                            'updated': blob.updated.isoformat(),
                            **metadata
                        },
                        'created_at': blob.time_created.isoformat(),
                        'relevance': 0.6,  # Lower than embedding matches
                        'source': 'GCS'
                    })
            except Exception:
                pass

    return results[:MAX_RESULTS]


def format_results(results: List[Dict[str, Any]]) -> str:
    """Format search results for display"""
    if not results:
        return "No results found."

    output = [f"Found {len(results)} results:\n"]

    for i, result in enumerate(results, 1):
        relevance = result['relevance']
        content = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
        source = result['source']
        created = result.get('created_at', 'Unknown')

        output.append(f"\n## Result {i} (Relevance: {relevance:.2%})")
        output.append(f"**Source**: {source}")
        output.append(f"**Created**: {created}")
        output.append(f"\n{content}\n")

        # Add GitHub link if available
        metadata = result.get('metadata', {})
        if 'github_url' in metadata:
            output.append(f"**GitHub**: {metadata['github_url']}")

        output.append("---")

    return "\n".join(output)


def main():
    if len(sys.argv) < 2:
        print("Usage: vertex_search.py <query>", file=sys.stderr)
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    try:
        # Initialize clients
        bq_client = bigquery.Client(project=PROJECT_ID)
        gcs_client = storage.Client(project=PROJECT_ID)

        # Get query embedding
        print(f"Searching for: {query}", file=sys.stderr)
        query_embedding = get_query_embedding(query)

        # Search BigQuery
        bq_results = search_bigquery(query_embedding, bq_client)

        # Search GCS
        gcs_results = search_gcs(query, gcs_client)

        # Combine and sort results
        all_results = bq_results + gcs_results
        all_results.sort(key=lambda x: x['relevance'], reverse=True)

        # Format and print
        output = format_results(all_results[:MAX_RESULTS])
        print(output)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
