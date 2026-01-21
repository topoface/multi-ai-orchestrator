#!/usr/bin/env python3
"""
Multi-AI Debate Engine
Orchestrates debates between Claude, Gemini, and Perplexity
"""
import sys
import json
import yaml
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
import anthropic
import google.generativeai as genai
import requests
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Supabase client (optional, only if configured)
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

# Load config
config_path = Path(__file__).parent.parent.parent.parent / "config" / "debate_config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)

# API Keys
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')

# Supabase (optional)
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')


class DebateEngine:
    def __init__(self, topic: str, expert_mode: bool = False, max_rounds: int = None):
        self.topic = topic
        self.expert_mode = expert_mode
        self.max_rounds = max_rounds or config['debate']['max_rounds']
        self.history: List[Dict[str, Any]] = []

        # Initialize AI clients
        self.claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        # Initialize Gemini (direct API)
        genai.configure(api_key=GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')

        # Initialize Supabase (optional)
        self.supabase_client = None
        if SUPABASE_AVAILABLE and SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
            try:
                self.supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
                print("✓ Supabase connected", file=sys.stderr)
            except Exception as e:
                print(f"⚠ Supabase connection failed: {e}", file=sys.stderr)

    def get_claude_response(self, prompt: str, context: str = "") -> str:
        """Get response from Claude"""
        system_prompt = f"""당신은 다른 AI 전문가와 함께 기술적 주제에 대해 **합의안을 만들기 위해** 대화하고 있습니다.

주제: {self.topic}

이전 대화 내용:
{context}

**목표**: 두 AI의 의견을 종합하여 **실용적이고 합의 가능한 최종 제안**을 작성하는 것입니다.

- 다른 AI의 좋은 점을 인정하세요
- 차이점이 있다면 절충안을 제시하세요
- 구체적이고 실행 가능한 제안을 작성하세요
- **반드시 한글로 답변해주세요**"""

        try:
            message = self.claude_client.messages.create(
                model=config['participants']['claude']['model'],
                max_tokens=config['participants']['claude']['max_tokens'],
                temperature=config['participants']['claude']['temperature'],
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text

        except Exception as e:
            return f"Error getting Claude response: {e}"

    def get_gemini_response(self, prompt: str, context: str = "") -> str:
        """Get response from Gemini"""
        full_prompt = f"""당신은 다른 AI 전문가와 함께 기술적 주제에 대해 **합의안을 만들기 위해** 대화하고 있습니다.

주제: {self.topic}

이전 대화 내용:
{context}

{prompt}

**목표**: 두 AI의 의견을 종합하여 **실용적이고 합의 가능한 최종 제안**을 작성하는 것입니다.

- 다른 AI의 좋은 점을 인정하세요
- 차이점이 있다면 절충안을 제시하세요
- 구체적이고 실행 가능한 제안을 작성하세요
- **반드시 한글로 답변해주세요**"""

        try:
            # Vertex AI SDK uses generation_config as a dict
            response = self.gemini_model.generate_content(
                full_prompt,
                generation_config={
                    'temperature': config['participants']['gemini']['temperature'],
                    'max_output_tokens': config['participants']['gemini']['max_tokens'],
                }
            )
            return response.text

        except Exception as e:
            return f"Error getting Gemini response: {e}"

    def get_perplexity_consensus(self, claude_pos: str, gemini_pos: str) -> str:
        """Get consensus proposal from Perplexity (mediator role)"""
        if not PERPLEXITY_API_KEY or not config['participants']['perplexity']['enabled']:
            return "Perplexity not available"

        prompt = f"""당신은 두 AI 전문가의 대화를 듣고 **최종 합의안을 도출하는 중재자**입니다.

주제: {self.topic}

Claude의 제안:
{claude_pos}

Gemini의 제안:
{gemini_pos}

**당신의 역할**: 두 제안의 장점을 결합하여 **실행 가능한 최종 합의안**을 작성하세요.

다음을 포함해주세요:
1. **최종 합의안** (구체적으로)
2. Claude 제안의 채택할 점
3. Gemini 제안의 채택할 점
4. 절충한 부분 (있다면)
5. 구현 시 주요 고려사항

**반드시 한글로 답변해주세요.**"""

        try:
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": config['participants']['perplexity']['model'],
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": config['participants']['perplexity']['temperature'],
                    "max_tokens": config['participants']['perplexity']['max_tokens']
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']

        except Exception as e:
            return f"Error getting Perplexity consensus: {e}"

    def calculate_consensus(self, claude_text: str, gemini_text: str) -> float:
        """Calculate consensus score using TF-IDF and cosine similarity"""
        if not claude_text or not gemini_text:
            return 0.0

        try:
            # Use TF-IDF vectorization with automatic stopword removal
            vectorizer = TfidfVectorizer(
                stop_words='english',
                lowercase=True,
                max_features=500,  # Limit to top 500 terms
                ngram_range=(1, 2),  # Use unigrams and bigrams
                min_df=1
            )

            # Create TF-IDF vectors for both texts
            tfidf_matrix = vectorizer.fit_transform([claude_text, gemini_text])

            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

            # Ensure result is between 0 and 1
            return max(0.0, min(1.0, similarity))

        except Exception as e:
            # Fallback to simple Jaccard similarity if TF-IDF fails
            print(f"⚠️ TF-IDF failed, using Jaccard fallback: {e}", file=sys.stderr)

            claude_words = set(claude_text.lower().split())
            gemini_words = set(gemini_text.lower().split())

            # Remove basic stopwords
            stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been'}
            claude_words -= stopwords
            gemini_words -= stopwords

            if not claude_words or not gemini_words:
                return 0.0

            intersection = len(claude_words & gemini_words)
            union = len(claude_words | gemini_words)

            return intersection / union if union > 0 else 0.0

    def conduct_debate(self) -> Dict[str, Any]:
        """Conduct collaborative discussion to reach consensus"""
        print(f"\n🤝 Starting collaborative discussion: {self.topic}\n", file=sys.stderr)
        print("Goal: Create a practical, consensus-based final proposal\n", file=sys.stderr)

        context = ""
        claude_final = ""
        gemini_final = ""
        perplexity_consensus = None

        for round_num in range(1, self.max_rounds + 1):
            print(f"=== Round {round_num}/{self.max_rounds} ===\n", file=sys.stderr)

            # Simple prompt for all rounds
            if round_num == 1:
                prompt = "이 주제에 대해 당신의 의견을 공유해주세요."
            else:
                prompt = "계속 대화를 이어가며 합의 가능한 제안을 만들어주세요."

            # Claude's turn
            print(f"Claude responding...", file=sys.stderr)
            claude_response = self.get_claude_response(prompt, context)
            self.history.append({"round": round_num, "ai": "Claude", "response": claude_response})
            context += f"\n\nClaude (Round {round_num}):\n{claude_response}"
            claude_final = claude_response

            # Gemini's turn
            print(f"Gemini responding...", file=sys.stderr)
            gemini_response = self.get_gemini_response(prompt, context)
            self.history.append({"round": round_num, "ai": "Gemini", "response": gemini_response})
            context += f"\n\nGemini (Round {round_num}):\n{gemini_response}"
            gemini_final = gemini_response

            # Round 5: Mandatory Perplexity call (mediator role)
            if round_num == 5:
                print("\n🎯 Round 5: Calling Perplexity for consensus mediation...\n", file=sys.stderr)
                perplexity_consensus = self.get_perplexity_consensus(claude_final, gemini_final)
                self.history.append({"round": round_num, "ai": "Perplexity", "response": perplexity_consensus})
                context += f"\n\n🎯 PERPLEXITY 최종 합의안:\n{perplexity_consensus}\n\n"
                print("✅ Perplexity consensus proposal received!\n", file=sys.stderr)

        # Calculate similarity score for reference
        consensus_score = self.calculate_consensus(claude_final, gemini_final)

        # Compile results
        result = {
            "topic": self.topic,
            "timestamp": datetime.utcnow().isoformat(),
            "rounds": self.max_rounds,
            "consensus_score": consensus_score,  # TF-IDF similarity for reference
            "status": "consensus_reached",
            "history": self.history,
            "claude_final_position": claude_final,
            "gemini_final_position": gemini_final,
            "perplexity_consensus": perplexity_consensus  # Main result
        }

        # Save to Supabase (if available)
        if self.supabase_client:
            self.save_to_supabase(result)

        return result

    def save_to_supabase(self, result: Dict[str, Any]) -> None:
        """Save debate result to Supabase"""
        if not self.supabase_client:
            return

        try:
            data = {
                'topic': self.topic,
                'claude_position': result['claude_final_position'],
                'gemini_position': result['gemini_final_position'],
                'consensus_score': result['consensus_score'],
                'rounds': result['rounds'],
                'metadata': {
                    'timestamp': result['timestamp'],
                    'status': result['status'],
                    'rounds_detail': result['history'],
                    'perplexity_consensus': result.get('perplexity_consensus'),
                    'expert_mode': self.expert_mode
                }
            }

            response = self.supabase_client.table('debate_results').insert(data).execute()
            if response.data:
                print(f"✓ Supabase: Debate saved (ID: {response.data[0]['id']})", file=sys.stderr)
        except Exception as e:
            print(f"⚠ Supabase save failed: {e}", file=sys.stderr)


def format_result(result: Dict[str, Any]) -> str:
    """Format debate result for display"""
    output = [
        f"\n{'='*80}",
        f"🤝 COLLABORATIVE DISCUSSION RESULT: {result['topic']}",
        f"{'='*80}\n",
        f"Timestamp: {result['timestamp']}",
        f"Rounds: {result['rounds']}",
        f"Similarity Score (reference): {result['consensus_score']:.2%}",
        f"Status: {result['status'].upper()}\n",
        f"{'='*80}",
        "\n## CLAUDE'S FINAL PROPOSAL\n",
        result['claude_final_position'],
        f"\n{'='*80}",
        "\n## GEMINI'S FINAL PROPOSAL\n",
        result['gemini_final_position'],
    ]

    if result.get('perplexity_consensus'):
        output.extend([
            f"\n{'='*80}",
            "\n## 🎯 PERPLEXITY 최종 합의안 (FINAL CONSENSUS)\n",
            result['perplexity_consensus']
        ])

    output.append(f"\n{'='*80}\n")

    return "\n".join(output)


def save_result(result: Dict[str, Any], output_path: Path = None):
    """Save debate result to files"""
    brain_dir = Path(__file__).parent.parent.parent.parent / "docs" / "brain"
    brain_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON
    json_path = output_path or brain_dir / f"debate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_path, 'w') as f:
        json.dump(result, f, indent=2)

    # Append to DECISIONS.md
    decisions_path = brain_dir / "DECISIONS.md"
    with open(decisions_path, 'a') as f:
        f.write(f"\n\n## Decision: {result['topic']}\n")
        f.write(f"**Date**: {result['timestamp']}\n")
        f.write(f"**Consensus**: {result['consensus_score']:.2%}\n")
        f.write(f"**Status**: {result['status']}\n\n")
        f.write(f"**Final Decision**:\n{result['claude_final_position'][:500]}...\n")
        f.write(f"\nFull details: [debate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json](debate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json)\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: debate_engine.py <topic> [--expert] [--quick]", file=sys.stderr)
        sys.exit(1)

    # Parse arguments
    args = sys.argv[1:]
    expert_mode = "--expert" in args
    quick_mode = "--quick" in args
    output_path = None

    if "--output" in args:
        idx = args.index("--output")
        if idx + 1 < len(args):
            output_path = Path(args[idx + 1])
            args = args[:idx] + args[idx + 2:]

    # Remove flags from topic
    topic = " ".join([arg for arg in args if not arg.startswith("--")])

    # Set rounds
    max_rounds = 2 if quick_mode else config['debate']['max_rounds']

    try:
        # Conduct debate
        engine = DebateEngine(topic, expert_mode, max_rounds)
        result = engine.conduct_debate()

        # Format and print
        output = format_result(result)
        print(output)

        # Save results
        save_result(result, output_path)
        print(f"\n✓ Results saved to docs/brain/", file=sys.stderr)

    except Exception as e:
        print(f"Debate error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
