#!/usr/bin/env python3
"""
GitHub ↔ Vertex AI Sync Manager
Bidirectional synchronization between GitHub and Vertex AI RAG
"""
import sys
import json
import yaml
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from google.cloud import bigquery, storage
import vertexai
from vertexai.language_models import TextEmbeddingModel

# Load config
config_path = Path(__file__).parent.parent.parent.parent / "config" / "vertex_config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)

PROJECT_ID = config['project_id']
LOCATION = config['location']
BRAIN_DIR = Path(__file__).parent.parent.parent.parent / "docs" / "brain"


def get_changed_files() -> List[Path]:
    """Get list of changed files in docs/brain/ using git diff"""
    try:
        # Get uncommitted changes
        result = subprocess.run(
            ["git", "diff", "--name-only", "docs/brain/"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent
        )
        uncommitted = result.stdout.strip().split("\n") if result.stdout.strip() else []

        # Get staged changes
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "docs/brain/"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent
        )
        staged = result.stdout.strip().split("\n") if result.stdout.strip() else []

        # Combine and convert to Path objects
        all_files = set(uncommitted + staged)
        return [Path(f) for f in all_files if f and f.endswith('.md')]

    except Exception as e:
        print(f"Error getting changed files: {e}", file=sys.stderr)
        return []


def get_all_brain_files() -> List[Path]:
    """Get all markdown files in docs/brain/"""
    if not BRAIN_DIR.exists():
        return []
    return list(BRAIN_DIR.glob("**/*.md"))


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for texts using Vertex AI"""
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = TextEmbeddingModel.from_pretrained(config['embedding']['model'])

    batch_size = config['embedding']['batch_size']
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        embeddings = model.get_embeddings(batch)
        all_embeddings.extend([emb.values for emb in embeddings])

    return all_embeddings


def sync_to_vertex(files: List[Path], bq_client: bigquery.Client, gcs_client: storage.Client) -> int:
    """Sync files from GitHub to Vertex AI"""
    if not files:
        print("No files to sync to Vertex AI")
        return 0

    bucket = gcs_client.bucket(config['gcs']['bucket'])
    synced_count = 0

    for file_path in files:
        if not file_path.exists():
            continue

        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Generate embedding
            print(f"Generating embedding for {file_path.name}...", file=sys.stderr)
            embeddings = generate_embeddings([content])
            embedding = embeddings[0]

            # Prepare metadata
            metadata = {
                'filename': file_path.name,
                'path': str(file_path),
                'type': 'brain_doc',
                'synced_at': datetime.utcnow().isoformat()
            }

            # Upload to BigQuery
            table_ref = f"{PROJECT_ID}.{config['bigquery']['knowledge_dataset']}.{config['bigquery']['knowledge_table']}"
            rows_to_insert = [{
                'content': content,
                'embedding': embedding,
                'metadata': json.dumps(metadata),
                'created_at': datetime.utcnow().isoformat()
            }]

            errors = bq_client.insert_rows_json(table_ref, rows_to_insert)
            if errors:
                print(f"BigQuery insert errors: {errors}", file=sys.stderr)
                continue

            # Backup to GCS
            blob = bucket.blob(f"{config['gcs']['folders']['context']}{file_path.name}")
            blob.upload_from_filename(str(file_path))
            blob.metadata = metadata
            blob.patch()

            synced_count += 1
            print(f"✓ Synced {file_path.name} to Vertex AI")

        except Exception as e:
            print(f"Error syncing {file_path}: {e}", file=sys.stderr)

    return synced_count


def sync_from_vertex(gcs_client: storage.Client) -> int:
    """Sync decisions from Vertex AI to GitHub"""
    bucket = gcs_client.bucket(config['gcs']['bucket'])
    synced_count = 0

    try:
        # Get latest decisions from GCS
        decisions_prefix = config['gcs']['folders']['decisions']
        blobs = list(bucket.list_blobs(prefix=decisions_prefix))

        if not blobs:
            print("No decisions to sync from Vertex AI")
            return 0

        # Sort by creation time, get most recent
        blobs.sort(key=lambda b: b.time_created, reverse=True)

        # Download and append to DECISIONS.md
        decisions_file = BRAIN_DIR / "DECISIONS.md"
        existing_content = ""
        if decisions_file.exists():
            with open(decisions_file, 'r', encoding='utf-8') as f:
                existing_content = f.read()

        for blob in blobs[:5]:  # Only sync 5 most recent
            if blob.name.endswith('/'):
                continue

            content = blob.download_as_text()

            # Check if already in file (avoid duplicates)
            if content.strip() in existing_content:
                continue

            # Append to file
            with open(decisions_file, 'a', encoding='utf-8') as f:
                f.write(f"\n\n## Decision from {blob.time_created.isoformat()}\n\n")
                f.write(content)
                f.write("\n")

            synced_count += 1
            print(f"✓ Synced decision from {blob.name}")

    except Exception as e:
        print(f"Error syncing from Vertex AI: {e}", file=sys.stderr)

    return synced_count


def main():
    mode = "both"
    initial_sync = False

    # Parse arguments
    if len(sys.argv) > 1:
        if "--to-vertex" in sys.argv:
            mode = "to-vertex"
        elif "--from-vertex" in sys.argv:
            mode = "from-vertex"
        if "--initial-sync" in sys.argv:
            initial_sync = True

    try:
        # Initialize clients
        bq_client = bigquery.Client(project=PROJECT_ID)
        gcs_client = storage.Client(project=PROJECT_ID)

        total_synced = 0

        # Sync GitHub → Vertex AI
        if mode in ["both", "to-vertex"]:
            print("Syncing GitHub → Vertex AI...", file=sys.stderr)
            if initial_sync:
                files = get_all_brain_files()
            else:
                files = get_changed_files()

            if files:
                count = sync_to_vertex(files, bq_client, gcs_client)
                total_synced += count
                print(f"Synced {count} files to Vertex AI")
            else:
                print("No changed files to sync")

        # Sync Vertex AI → GitHub
        if mode in ["both", "from-vertex"]:
            print("\nSyncing Vertex AI → GitHub...", file=sys.stderr)
            count = sync_from_vertex(gcs_client)
            total_synced += count
            print(f"Synced {count} decisions from Vertex AI")

        print(f"\n✓ Total synced: {total_synced} items")

    except Exception as e:
        print(f"Sync error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
