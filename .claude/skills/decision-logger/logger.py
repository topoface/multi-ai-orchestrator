#!/usr/bin/env python3
"""
Decision Logger
Automatically log important decisions to GitHub and Vertex AI
"""
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List
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


class DecisionLogger:
    def __init__(self):
        self.bq_client = bigquery.Client(project=PROJECT_ID)
        self.gcs_client = storage.Client(project=PROJECT_ID)
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        self.embedding_model = TextEmbeddingModel.from_pretrained(config['embedding']['model'])

    def format_decision(self, decision_data: Dict[str, Any]) -> str:
        """Format decision in consistent markdown structure"""
        title = decision_data.get('title', 'Untitled Decision')
        date = decision_data.get('date', datetime.utcnow().isoformat())
        consensus = decision_data.get('consensus', 0.0)
        priority = decision_data.get('priority', 'medium')
        tags = decision_data.get('tags', [])

        output = [
            f"## Decision: {title}\n",
            f"**Date**: {date}",
            f"**Consensus**: {consensus:.2%}",
            f"**Priority**: {priority}",
            f"**Tags**: {', '.join(tags)}\n",
        ]

        # What was decided
        if 'decision' in decision_data:
            output.extend([
                "### What Was Decided",
                decision_data['decision'],
                ""
            ])

        # Why
        if 'reasoning' in decision_data:
            output.extend([
                "### Why This Decision",
                decision_data['reasoning'],
                ""
            ])

        # Alternatives
        if 'alternatives' in decision_data:
            output.append("### Alternatives Considered")
            for i, alt in enumerate(decision_data['alternatives'], 1):
                output.append(f"{i}. {alt}")
            output.append("")

        # Participants
        if 'participants' in decision_data:
            output.append("### Participants")
            for participant, position in decision_data['participants'].items():
                output.append(f"- **{participant}**: {position[:200]}...")
            output.append("")

        # Implementation notes
        if 'implementation_notes' in decision_data:
            output.extend([
                "### Implementation Notes",
                decision_data['implementation_notes'],
                ""
            ])

        output.append("---\n")

        return "\n".join(output)

    def save_to_github(self, formatted_decision: str):
        """Save decision to GitHub docs/brain/DECISIONS.md"""
        BRAIN_DIR.mkdir(parents=True, exist_ok=True)
        decisions_file = BRAIN_DIR / "DECISIONS.md"

        # Create file with header if it doesn't exist
        if not decisions_file.exists():
            with open(decisions_file, 'w') as f:
                f.write("# Decision Log\n\n")
                f.write("This file contains all important decisions made by the Multi-AI system.\n\n")
                f.write("---\n\n")

        # Append decision
        with open(decisions_file, 'a') as f:
            f.write(formatted_decision)

        print(f"✓ Saved to {decisions_file}")

    def save_to_vertex(self, decision_data: Dict[str, Any], formatted_decision: str):
        """Save decision to Vertex AI (BigQuery + GCS)"""
        # Generate embedding
        embedding = self.embedding_model.get_embeddings([formatted_decision])[0].values

        # Prepare metadata
        metadata = {
            'type': 'decision',
            'title': decision_data.get('title', 'Untitled'),
            'date': decision_data.get('date', datetime.utcnow().isoformat()),
            'consensus': decision_data.get('consensus', 0.0),
            'priority': decision_data.get('priority', 'medium'),
            'tags': decision_data.get('tags', [])
        }

        # Save to BigQuery
        table_ref = f"{PROJECT_ID}.{config['bigquery']['knowledge_dataset']}.{config['bigquery']['knowledge_table']}"
        rows_to_insert = [{
            'content': formatted_decision,
            'embedding': embedding,
            'metadata': json.dumps(metadata),
            'created_at': datetime.utcnow().isoformat()
        }]

        errors = self.bq_client.insert_rows_json(table_ref, rows_to_insert)
        if errors:
            print(f"⚠ BigQuery insert errors: {errors}", file=sys.stderr)
        else:
            print("✓ Saved to BigQuery")

        # Save to GCS
        bucket = self.gcs_client.bucket(config['gcs']['bucket'])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        blob = bucket.blob(f"{config['gcs']['folders']['decisions']}decision_{timestamp}.json")

        blob.upload_from_string(
            json.dumps(decision_data, indent=2),
            content_type='application/json'
        )
        blob.metadata = metadata
        blob.patch()

        print(f"✓ Saved to GCS: decision_{timestamp}.json")

    def log_decision(self, decision_data: Dict[str, Any]):
        """Log a decision to all storage locations"""
        # Format decision
        formatted = self.format_decision(decision_data)

        # Save to GitHub
        self.save_to_github(formatted)

        # Save to Vertex AI
        self.save_to_vertex(decision_data, formatted)

        print(f"\n✓ Decision logged successfully: {decision_data.get('title', 'Untitled')}")


def parse_manual_decision(args: List[str]) -> Dict[str, Any]:
    """Parse manual decision from command line arguments"""
    decision_data = {
        'title': 'Manual Decision',
        'date': datetime.utcnow().isoformat(),
        'decision': '',
        'reasoning': '',
        'alternatives': [],
        'priority': 'medium',
        'tags': [],
        'consensus': 1.0  # Manual decisions are 100% consensus
    }

    i = 0
    while i < len(args):
        if args[i] == '--title' and i + 1 < len(args):
            decision_data['title'] = args[i + 1]
            i += 2
        elif args[i] == '--decision' and i + 1 < len(args):
            decision_data['decision'] = args[i + 1]
            i += 2
        elif args[i] == '--reason' and i + 1 < len(args):
            decision_data['reasoning'] = args[i + 1]
            i += 2
        elif args[i] == '--alternatives' and i + 1 < len(args):
            decision_data['alternatives'] = [alt.strip() for alt in args[i + 1].split(',')]
            i += 2
        elif args[i] == '--priority' and i + 1 < len(args):
            decision_data['priority'] = args[i + 1]
            i += 2
        elif args[i] == '--tags' and i + 1 < len(args):
            decision_data['tags'] = [tag.strip() for tag in args[i + 1].split(',')]
            i += 2
        else:
            i += 1

    return decision_data


def load_debate_result(result_path: Path) -> Dict[str, Any]:
    """Load debate result from JSON file"""
    with open(result_path, 'r') as f:
        result = json.load(f)

    # Convert debate result to decision format
    decision_data = {
        'title': result.get('topic', 'Untitled'),
        'date': result.get('timestamp', datetime.utcnow().isoformat()),
        'consensus': result.get('consensus_score', 0.0),
        'decision': result.get('claude_final_position', ''),
        'reasoning': result.get('gemini_final_position', ''),
        'participants': {
            'Claude': result.get('claude_final_position', '')[:200],
            'Gemini': result.get('gemini_final_position', '')[:200]
        },
        'priority': 'high' if result.get('consensus_score', 0) >= 0.85 else 'medium',
        'tags': ['debate', 'multi-ai']
    }

    if result.get('perplexity_judgment'):
        decision_data['participants']['Perplexity'] = result['perplexity_judgment'][:200]
        decision_data['implementation_notes'] = result['perplexity_judgment']

    return decision_data


def main():
    if len(sys.argv) < 2:
        # Try to find latest debate result
        brain_dir = Path(__file__).parent.parent.parent.parent / "docs" / "brain"
        debate_files = sorted(brain_dir.glob("debate_*.json"))

        if debate_files:
            latest_debate = debate_files[-1]
            print(f"Logging latest debate result: {latest_debate.name}", file=sys.stderr)
            logger = DecisionLogger()
            decision_data = load_debate_result(latest_debate)
            logger.log_decision(decision_data)
        else:
            print("Usage: logger.py [--manual | --file <path>]", file=sys.stderr)
            print("  --manual: Log manual decision with --title, --reason, etc.", file=sys.stderr)
            print("  --file: Log from debate result JSON file", file=sys.stderr)
            sys.exit(1)
        return

    logger = DecisionLogger()

    if '--manual' in sys.argv:
        # Parse manual decision
        decision_data = parse_manual_decision(sys.argv)
        logger.log_decision(decision_data)

    elif '--file' in sys.argv:
        idx = sys.argv.index('--file')
        if idx + 1 < len(sys.argv):
            result_path = Path(sys.argv[idx + 1])
            if result_path.exists():
                decision_data = load_debate_result(result_path)
                logger.log_decision(decision_data)
            else:
                print(f"Error: File not found: {result_path}", file=sys.stderr)
                sys.exit(1)
        else:
            print("Error: --file requires a path argument", file=sys.stderr)
            sys.exit(1)

    else:
        print("Error: Invalid arguments", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
