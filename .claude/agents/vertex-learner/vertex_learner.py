#!/usr/bin/env python3
"""
Vertex AI Learner
Manages knowledge learning and RAG quality in Vertex AI
"""
import sys
import json
import yaml
import hashlib
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
BATCH_SIZE = config['embedding']['batch_size']


class VertexLearner:
    def __init__(self):
        self.bq_client = bigquery.Client(project=PROJECT_ID)
        self.gcs_client = storage.Client(project=PROJECT_ID)
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        self.embedding_model = TextEmbeddingModel.from_pretrained(config['embedding']['model'])

    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text before embedding"""
        # Remove excessive whitespace
        text = " ".join(text.split())

        # Truncate if too long (max 10,000 chars for gecko)
        if len(text) > 10000:
            text = text[:10000] + "..."

        return text

    def generate_content_hash(self, text: str) -> str:
        """Generate SHA256 hash of content for deduplication"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def check_duplicate(self, content_hash: str) -> bool:
        """Check if content already exists in BigQuery"""
        query = f"""
        SELECT COUNT(*) as count
        FROM `{PROJECT_ID}.{config['bigquery']['knowledge_dataset']}.{config['bigquery']['knowledge_table']}`
        WHERE JSON_EXTRACT_SCALAR(metadata, '$.content_hash') = '{content_hash}'
        """

        try:
            result = self.bq_client.query(query).result()
            for row in result:
                return row.count > 0
        except Exception:
            pass

        return False

    def learn_from_text(self, text: str, metadata: Dict[str, Any] = None):
        """Learn from a single text"""
        # Preprocess
        text = self.preprocess_text(text)

        # Check duplicate
        content_hash = self.generate_content_hash(text)
        if self.check_duplicate(content_hash):
            print(f"⚠ Duplicate detected, skipping: {content_hash[:8]}...")
            return

        # Generate embedding
        try:
            embeddings = self.embedding_model.get_embeddings([text])
            embedding = embeddings[0].values
        except Exception as e:
            print(f"Error generating embedding: {e}", file=sys.stderr)
            return

        # Prepare metadata
        if metadata is None:
            metadata = {}
        metadata['content_hash'] = content_hash
        metadata['learned_at'] = datetime.utcnow().isoformat()

        # Insert into BigQuery
        self._insert_to_bigquery(text, embedding, metadata)

        # Backup to GCS
        self._backup_to_gcs(text, metadata)

        print(f"✓ Learned: {content_hash[:8]}...")

    def learn_from_file(self, file_path: Path, metadata: Dict[str, Any] = None):
        """Learn from a file"""
        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            # Add file metadata
            file_metadata = metadata or {}
            file_metadata['source_file'] = str(file_path)
            file_metadata['filename'] = file_path.name

            self.learn_from_text(text, file_metadata)

        except Exception as e:
            print(f"Error learning from file {file_path}: {e}", file=sys.stderr)

    def batch_learn(self, texts: List[str], metadata_list: List[Dict[str, Any]] = None):
        """Learn from multiple texts efficiently"""
        if not texts:
            return

        if metadata_list is None:
            metadata_list = [{}] * len(texts)

        # Process in batches
        for i in range(0, len(texts), BATCH_SIZE):
            batch_texts = texts[i:i + BATCH_SIZE]
            batch_metadata = metadata_list[i:i + BATCH_SIZE]

            print(f"Processing batch {i // BATCH_SIZE + 1}...", file=sys.stderr)

            # Preprocess batch
            processed_texts = [self.preprocess_text(t) for t in batch_texts]

            # Check duplicates
            to_embed = []
            to_embed_metadata = []

            for text, meta in zip(processed_texts, batch_metadata):
                content_hash = self.generate_content_hash(text)
                if not self.check_duplicate(content_hash):
                    to_embed.append(text)
                    meta['content_hash'] = content_hash
                    meta['learned_at'] = datetime.utcnow().isoformat()
                    to_embed_metadata.append(meta)

            if not to_embed:
                print("  All texts are duplicates, skipping batch")
                continue

            # Generate embeddings
            try:
                embeddings = self.embedding_model.get_embeddings(to_embed)
                embedding_values = [emb.values for emb in embeddings]
            except Exception as e:
                print(f"  Error generating embeddings: {e}", file=sys.stderr)
                continue

            # Insert to BigQuery
            for text, embedding, meta in zip(to_embed, embedding_values, to_embed_metadata):
                self._insert_to_bigquery(text, embedding, meta)
                self._backup_to_gcs(text, meta)

            print(f"  ✓ Learned {len(to_embed)} new texts")

    def _insert_to_bigquery(self, text: str, embedding: List[float], metadata: Dict[str, Any]):
        """Insert into BigQuery"""
        table_ref = f"{PROJECT_ID}.{config['bigquery']['knowledge_dataset']}.{config['bigquery']['knowledge_table']}"

        rows_to_insert = [{
            'content': text,
            'embedding': embedding,
            'metadata': json.dumps(metadata),
            'created_at': datetime.utcnow().isoformat()
        }]

        errors = self.bq_client.insert_rows_json(table_ref, rows_to_insert)
        if errors:
            print(f"  ⚠ BigQuery insert errors: {errors}", file=sys.stderr)

    def _backup_to_gcs(self, text: str, metadata: Dict[str, Any]):
        """Backup to GCS"""
        bucket = self.gcs_client.bucket(config['gcs']['bucket'])
        content_hash = metadata.get('content_hash', self.generate_content_hash(text))

        blob = bucket.blob(f"{config['gcs']['folders']['context']}{content_hash[:16]}.txt")
        blob.upload_from_string(text)
        blob.metadata = metadata
        blob.patch()

    def deduplicate_knowledge(self):
        """Remove duplicate embeddings from BigQuery"""
        print("Deduplicating knowledge base...", file=sys.stderr)

        query = f"""
        DELETE FROM `{PROJECT_ID}.{config['bigquery']['knowledge_dataset']}.{config['bigquery']['knowledge_table']}`
        WHERE created_at NOT IN (
            SELECT MAX(created_at)
            FROM `{PROJECT_ID}.{config['bigquery']['knowledge_dataset']}.{config['bigquery']['knowledge_table']}`
            GROUP BY JSON_EXTRACT_SCALAR(metadata, '$.content_hash')
        )
        """

        try:
            job = self.bq_client.query(query)
            job.result()
            print(f"✓ Deduplication complete")
        except Exception as e:
            print(f"Error deduplicating: {e}", file=sys.stderr)

    def monitor_quality(self):
        """Monitor RAG quality metrics"""
        print("Monitoring RAG quality...\n", file=sys.stderr)

        # Count total embeddings
        count_query = f"""
        SELECT COUNT(*) as total
        FROM `{PROJECT_ID}.{config['bigquery']['knowledge_dataset']}.{config['bigquery']['knowledge_table']}`
        """

        try:
            result = self.bq_client.query(count_query).result()
            for row in result:
                print(f"Total embeddings: {row.total}")
        except Exception as e:
            print(f"Error counting embeddings: {e}", file=sys.stderr)

        # Check staleness
        staleness_query = f"""
        SELECT MIN(created_at) as oldest, MAX(created_at) as newest
        FROM `{PROJECT_ID}.{config['bigquery']['knowledge_dataset']}.{config['bigquery']['knowledge_table']}`
        """

        try:
            result = self.bq_client.query(staleness_query).result()
            for row in result:
                print(f"Oldest embedding: {row.oldest}")
                print(f"Newest embedding: {row.newest}")
        except Exception as e:
            print(f"Error checking staleness: {e}", file=sys.stderr)


def main():
    if len(sys.argv) < 2:
        print("Usage: vertex_learner.py <command> [options]", file=sys.stderr)
        print("\nCommands:", file=sys.stderr)
        print("  learn --text <text> [--metadata <json>]", file=sys.stderr)
        print("  learn-file --file <path> [--metadata <json>]", file=sys.stderr)
        print("  batch-learn --files <pattern>", file=sys.stderr)
        print("  deduplicate", file=sys.stderr)
        print("  monitor-quality", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    learner = VertexLearner()

    try:
        if command == 'learn':
            text = ""
            metadata = {}

            i = 2
            while i < len(sys.argv):
                if sys.argv[i] == '--text' and i + 1 < len(sys.argv):
                    text = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == '--metadata' and i + 1 < len(sys.argv):
                    metadata = json.loads(sys.argv[i + 1])
                    i += 2
                else:
                    i += 1

            if text:
                learner.learn_from_text(text, metadata)

        elif command == 'learn-file':
            file_path = None
            metadata = {}

            i = 2
            while i < len(sys.argv):
                if sys.argv[i] == '--file' and i + 1 < len(sys.argv):
                    file_path = Path(sys.argv[i + 1])
                    i += 2
                elif sys.argv[i] == '--metadata' and i + 1 < len(sys.argv):
                    metadata = json.loads(sys.argv[i + 1])
                    i += 2
                else:
                    i += 1

            if file_path:
                learner.learn_from_file(file_path, metadata)

        elif command == 'batch-learn':
            pattern = ""

            i = 2
            while i < len(sys.argv):
                if sys.argv[i] == '--files' and i + 1 < len(sys.argv):
                    pattern = sys.argv[i + 1]
                    i += 2
                else:
                    i += 1

            if pattern:
                from glob import glob
                files = [Path(f) for f in glob(pattern)]
                texts = []
                metadata_list = []

                for f in files:
                    try:
                        with open(f, 'r') as file:
                            texts.append(file.read())
                            metadata_list.append({'source_file': str(f), 'filename': f.name})
                    except Exception as e:
                        print(f"Error reading {f}: {e}", file=sys.stderr)

                learner.batch_learn(texts, metadata_list)

        elif command == 'deduplicate':
            learner.deduplicate_knowledge()

        elif command == 'monitor-quality':
            learner.monitor_quality()

        else:
            print(f"Unknown command: {command}", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
