#!/usr/bin/env python3
"""
Upload Multi-AI Debate Results to Vertex AI
Extracts debate results and decisions, creates embeddings, uploads to BigQuery
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import vertexai
from vertexai.language_models import TextEmbeddingModel
from google.cloud import bigquery
from dotenv import load_dotenv

# Load environment
load_dotenv()
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'phsysics')
GCP_REGION = os.getenv('GCP_REGION', 'us-central1')

# Initialize Vertex AI
vertexai.init(project=GCP_PROJECT_ID, location=GCP_REGION)

# BigQuery configuration
DATASET_ID = 'multi_ai_knowledge'
TABLE_ID = 'debate_embeddings'
FULL_TABLE_ID = f'{GCP_PROJECT_ID}.{DATASET_ID}.{TABLE_ID}'

class VertexAIUploader:
    def __init__(self):
        self.embedding_model = TextEmbeddingModel.from_pretrained('textembedding-gecko@003')
        self.bq_client = bigquery.Client(project=GCP_PROJECT_ID)
        self.ensure_dataset_exists()

    def ensure_dataset_exists(self):
        """Create dataset and table if not exists"""
        try:
            # Create dataset
            dataset = bigquery.Dataset(f'{GCP_PROJECT_ID}.{DATASET_ID}')
            dataset.location = GCP_REGION
            self.bq_client.create_dataset(dataset, exists_ok=True)
            print(f"✓ Dataset {DATASET_ID} ready")

            # Create table schema
            schema = [
                bigquery.SchemaField("doc_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("doc_type", "STRING", mode="REQUIRED"),  # debate, decision, context
                bigquery.SchemaField("title", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("content", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED"),
                bigquery.SchemaField("metadata", "JSON", mode="NULLABLE"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            ]

            table = bigquery.Table(FULL_TABLE_ID, schema=schema)
            self.bq_client.create_table(table, exists_ok=True)
            print(f"✓ Table {TABLE_ID} ready")

        except Exception as e:
            print(f"⚠ Dataset/Table setup warning: {e}")

    def extract_debate_data(self) -> List[Dict[str, Any]]:
        """Extract data from docs/brain/ debate JSONs"""
        docs = []
        debate_dir = Path(__file__).parent.parent / 'docs' / 'brain'

        # Process debate JSON files
        for json_file in debate_dir.glob('debate_*.json'):
            try:
                with open(json_file) as f:
                    debate = json.load(f)

                # Extract key information
                doc_id = json_file.stem
                title = debate.get('topic', 'Unknown topic')

                # Combine all responses into searchable content
                content_parts = [f"주제: {title}"]

                # Add final positions
                if 'claude_final_position' in debate:
                    content_parts.append(f"\nClaude 입장:\n{debate['claude_final_position']}")
                if 'gemini_final_position' in debate:
                    content_parts.append(f"\nGemini 입장:\n{debate['gemini_final_position']}")

                # Add perplexity judgment
                if 'perplexity_judgment' in debate:
                    judgment = debate['perplexity_judgment']
                    if isinstance(judgment, dict):
                        content_parts.append(f"\nPerplexity 판정: {judgment.get('full_response', '')}")

                content = '\n'.join(content_parts)

                docs.append({
                    'doc_id': doc_id,
                    'doc_type': 'debate',
                    'title': title,
                    'content': content,
                    'metadata': {
                        'status': debate.get('status', 'unknown'),
                        'consensus_score': debate.get('consensus_score', 0),
                        'total_rounds': debate.get('total_rounds', 0),
                        'timestamp': debate.get('timestamp', '')
                    },
                    'created_at': debate.get('timestamp', datetime.now().isoformat())
                })

            except Exception as e:
                print(f"⚠ Skip {json_file.name}: {e}")

        # Process DECISIONS.md
        decisions_file = debate_dir / 'DECISIONS.md'
        if decisions_file.exists():
            try:
                content = decisions_file.read_text()
                docs.append({
                    'doc_id': 'decisions_master',
                    'doc_type': 'decision',
                    'title': 'Multi-AI 결정 사항 모음',
                    'content': content,
                    'metadata': {'source': 'DECISIONS.md'},
                    'created_at': datetime.now().isoformat()
                })
            except Exception as e:
                print(f"⚠ Skip DECISIONS.md: {e}")

        # Process CONTEXT.md
        context_file = debate_dir / 'CONTEXT.md'
        if context_file.exists():
            try:
                content = context_file.read_text()
                docs.append({
                    'doc_id': 'context_master',
                    'doc_type': 'context',
                    'title': 'Multi-AI Orchestrator 컨텍스트',
                    'content': content,
                    'metadata': {'source': 'CONTEXT.md'},
                    'created_at': datetime.now().isoformat()
                })
            except Exception as e:
                print(f"⚠ Skip CONTEXT.md: {e}")

        return docs

    def create_embeddings(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create embeddings for documents"""
        print(f"\n📊 Creating embeddings for {len(docs)} documents...")

        # Batch process (max 5 at a time for API limits)
        batch_size = 5
        for i in range(0, len(docs), batch_size):
            batch = docs[i:i+batch_size]
            texts = [doc['content'][:10000] for doc in batch]  # Limit to 10K chars

            try:
                embeddings = self.embedding_model.get_embeddings(texts)
                for doc, embedding in zip(batch, embeddings):
                    doc['embedding'] = embedding.values
                print(f"  ✓ Batch {i//batch_size + 1}/{(len(docs)-1)//batch_size + 1}")
            except Exception as e:
                print(f"  ⚠ Batch {i//batch_size + 1} failed: {e}")

        return docs

    def upload_to_bigquery(self, docs: List[Dict[str, Any]]):
        """Upload documents with embeddings to BigQuery"""
        print(f"\n⬆️  Uploading {len(docs)} documents to BigQuery...")

        # Prepare rows
        rows = []
        for doc in docs:
            if 'embedding' not in doc:
                continue

            rows.append({
                'doc_id': doc['doc_id'],
                'doc_type': doc['doc_type'],
                'title': doc['title'],
                'content': doc['content'][:50000],  # BigQuery limit
                'embedding': doc['embedding'],
                'metadata': doc['metadata'],
                'created_at': doc['created_at']
            })

        if not rows:
            print("⚠ No rows to upload")
            return

        # Insert rows
        try:
            errors = self.bq_client.insert_rows_json(FULL_TABLE_ID, rows)
            if errors:
                print(f"⚠ Insert errors: {errors}")
            else:
                print(f"✅ Uploaded {len(rows)} documents to BigQuery")
        except Exception as e:
            print(f"❌ Upload failed: {e}")

    def run(self):
        """Run full pipeline"""
        print("🚀 Starting Vertex AI upload pipeline...\n")

        # Step 1: Extract data
        print("📂 Extracting data from docs/brain/...")
        docs = self.extract_debate_data()
        print(f"✓ Found {len(docs)} documents")

        # Step 2: Create embeddings
        docs = self.create_embeddings(docs)

        # Step 3: Upload to BigQuery
        self.upload_to_bigquery(docs)

        print(f"\n✅ Pipeline complete!")
        print(f"   Dataset: {DATASET_ID}")
        print(f"   Table: {TABLE_ID}")
        print(f"   Total docs: {len(docs)}")

if __name__ == "__main__":
    uploader = VertexAIUploader()
    uploader.run()
