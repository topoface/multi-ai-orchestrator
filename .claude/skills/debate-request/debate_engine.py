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

    def get_claude_response(self, prompt: str, context: str = "", ask_agreement: bool = False) -> str:
        """Get response from Claude"""
        base_prompt = f"""You are exploring a technical topic with other AI experts.
Topic: {self.topic}

Previous discussion:
{context}

Share your analysis objectively. Consider multiple perspectives and their merits."""

        if ask_agreement:
            system_prompt = base_prompt + """

IMPORTANT: After your analysis, you MUST explicitly state:
1. Your agreement level with the other AI's position:
   AGREEMENT: [AGREE / PARTIAL / DISAGREE]

2. Whether you think we need expert input:
   EXPERT_NEEDED: [YES / NO]

Explain your reasoning for both decisions."""
        else:
            system_prompt = base_prompt + """

Format your response clearly with your position, reasoning, and evidence."""

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

    def get_gemini_response(self, prompt: str, context: str = "", ask_agreement: bool = False) -> str:
        """Get response from Gemini"""
        base_prompt = f"""You are exploring a technical topic with other AI experts.
Topic: {self.topic}

Previous discussion:
{context}

{prompt}

Share your analysis objectively. Consider multiple perspectives and their merits."""

        if ask_agreement:
            full_prompt = base_prompt + """

IMPORTANT: After your analysis, you MUST explicitly state:
1. Your agreement level with the other AI's position:
   AGREEMENT: [AGREE / PARTIAL / DISAGREE]

2. Whether you think we need expert input:
   EXPERT_NEEDED: [YES / NO]

Explain your reasoning for both decisions."""
        else:
            full_prompt = base_prompt

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

    def get_perplexity_judgment(self, claude_pos: str, gemini_pos: str) -> str:
        """Get expert judgment from Perplexity"""
        if not PERPLEXITY_API_KEY or not config['participants']['perplexity']['enabled']:
            return "Perplexity not available"

        prompt = f"""Given this technical debate:

Topic: {self.topic}

Claude's position:
{claude_pos}

Gemini's position:
{gemini_pos}

As an expert, analyze both positions and provide:
1. Strengths of each approach
2. Weaknesses of each approach
3. Your recommended decision
4. Key considerations for implementation

Be objective and focus on technical merits."""

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
            return f"Error getting Perplexity judgment: {e}"

    def parse_agreement(self, text: str) -> Tuple[str, bool]:
        """Parse explicit agreement level and expert need from AI response

        Returns:
            (agreement_level, needs_expert)
            agreement_level: 'AGREE', 'PARTIAL', 'DISAGREE', or 'UNKNOWN'
            needs_expert: True if expert is needed
        """
        agreement = 'UNKNOWN'
        needs_expert = False

        text_upper = text.upper()

        # Parse agreement level (flexible parsing)
        if 'AGREEMENT:' in text_upper:
            # Extract the line with AGREEMENT
            for line in text.upper().split('\n'):
                if 'AGREEMENT:' in line:
                    # Check for agreement indicators
                    if 'STRONG AGREEMENT' in line or 'FULL AGREEMENT' in line or ('AGREE' in line and 'DISAGREE' not in line and 'PARTIAL' not in line):
                        agreement = 'AGREE'
                    elif 'PARTIAL' in line or 'MOSTLY' in line:
                        agreement = 'PARTIAL'
                    elif 'DISAGREE' in line and 'PARTIAL' not in line:
                        agreement = 'DISAGREE'
                    break

        # Parse expert need (flexible)
        if 'EXPERT_NEEDED:' in text_upper:
            for line in text.upper().split('\n'):
                if 'EXPERT_NEEDED:' in line:
                    if 'YES' in line and 'NO' not in line:
                        needs_expert = True
                    elif 'NO' in line:
                        needs_expert = False
                    break

        return agreement, needs_expert

    def check_consensus_reached(self, claude_agreement: str, gemini_agreement: str) -> Tuple[bool, str]:
        """Check if consensus is reached based on explicit agreements

        Returns:
            (consensus_reached, status)
        """
        # Both agree -> consensus!
        if claude_agreement == 'AGREE' and gemini_agreement == 'AGREE':
            return True, 'consensus'

        # Both partial -> good enough consensus
        if claude_agreement in ['AGREE', 'PARTIAL'] and gemini_agreement in ['AGREE', 'PARTIAL']:
            return True, 'partial_consensus'

        # Any disagree -> no consensus
        if claude_agreement == 'DISAGREE' or gemini_agreement == 'DISAGREE':
            return False, 'disagreement'

        # Unknown -> continue discussion
        return False, 'unclear'

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
        """Conduct the multi-round debate with explicit agreement checks"""
        print(f"\n🔥 Starting collaborative discussion: {self.topic}\n", file=sys.stderr)

        context = ""
        claude_final = ""
        gemini_final = ""
        consensus_reached = False
        expert_called = False

        for round_num in range(1, self.max_rounds + 1):
            print(f"=== Round {round_num}/{self.max_rounds} ===\n", file=sys.stderr)

            # Rounds 1-2: Free discussion without agreement check
            ask_for_agreement = (round_num >= 3)

            if round_num == 1:
                # Round 1: Initial perspectives
                print("Claude sharing perspective...", file=sys.stderr)
                prompt = f"What's your understanding of: {self.topic}"
                claude_response = self.get_claude_response(prompt, context)
                self.history.append({"round": round_num, "ai": "Claude", "response": claude_response})
                context += f"\n\nClaude (Round {round_num}):\n{claude_response}"
                claude_final = claude_response

                print("Gemini sharing perspective...", file=sys.stderr)
                prompt = f"What's your understanding of this topic?"
                gemini_response = self.get_gemini_response(prompt, context)
                self.history.append({"round": round_num, "ai": "Gemini", "response": gemini_response})
                context += f"\n\nGemini (Round {round_num}):\n{gemini_response}"
                gemini_final = gemini_response

            elif round_num == 2:
                # Round 2: Continue discussion
                print("Continuing discussion...", file=sys.stderr)
                prompt = f"Based on our discussion so far, what are your thoughts?"
                gemini_response = self.get_gemini_response(prompt, context)
                self.history.append({"round": round_num, "ai": "Gemini", "response": gemini_response})
                context += f"\n\nGemini (Round {round_num}):\n{gemini_response}"
                gemini_final = gemini_response

                prompt = f"Your thoughts on the discussion?"
                claude_response = self.get_claude_response(prompt, context)
                self.history.append({"round": round_num, "ai": "Claude", "response": claude_response})
                context += f"\n\nClaude (Round {round_num}):\n{claude_response}"
                claude_final = claude_response

            else:
                # Round 3+: Ask for explicit agreement
                print(f"Round {round_num}: Checking agreement...", file=sys.stderr)
                prompt = f"Based on our discussion, what are your thoughts? Do you agree with the other AI's position?"

                claude_response = self.get_claude_response(prompt, context, ask_agreement=ask_for_agreement)
                self.history.append({"round": round_num, "ai": "Claude", "response": claude_response})
                context += f"\n\nClaude (Round {round_num}):\n{claude_response}"
                claude_final = claude_response

                gemini_response = self.get_gemini_response(prompt, context, ask_agreement=ask_for_agreement)
                self.history.append({"round": round_num, "ai": "Gemini", "response": gemini_response})
                context += f"\n\nGemini (Round {round_num}):\n{gemini_response}"
                gemini_final = gemini_response

                # Parse explicit agreements
                if ask_for_agreement:
                    claude_agreement, claude_needs_expert = self.parse_agreement(claude_response)
                    gemini_agreement, gemini_needs_expert = self.parse_agreement(gemini_response)

                    print(f"  Claude: {claude_agreement}, Expert: {claude_needs_expert}", file=sys.stderr)
                    print(f"  Gemini: {gemini_agreement}, Expert: {gemini_needs_expert}\n", file=sys.stderr)

                    # Check consensus
                    consensus_reached, consensus_status = self.check_consensus_reached(claude_agreement, gemini_agreement)

                    if consensus_reached:
                        print(f"✅ Explicit consensus reached ({consensus_status})! Ending discussion.\n", file=sys.stderr)

                        # Calculate TF-IDF consensus score for reference
                        consensus_score = self.calculate_consensus(claude_final, gemini_final)

                        result = {
                            "topic": self.topic,
                            "timestamp": datetime.utcnow().isoformat(),
                            "rounds": round_num,
                            "consensus_type": consensus_status,
                            "consensus_score": consensus_score,  # TF-IDF score for reference
                            "claude_agreement": claude_agreement,
                            "gemini_agreement": gemini_agreement,
                            "status": "consensus",
                            "history": self.history,
                            "claude_final_position": claude_final,
                            "gemini_final_position": gemini_final,
                        }
                        if self.supabase_client:
                            self.save_to_supabase(result)
                        return result

                    # Check if both want expert
                    if claude_needs_expert and gemini_needs_expert and round_num <= 5:
                        print("🚨 Both AIs request expert! Calling Perplexity...\n", file=sys.stderr)
                        perplexity_judgment = self.get_perplexity_judgment(claude_final, gemini_final)
                        self.history.append({"round": round_num, "ai": "Perplexity", "response": perplexity_judgment})
                        context += f"\n\n🎯 PERPLEXITY EXPERT JUDGMENT:\n{perplexity_judgment}\n\n"
                        expert_called = True
                        print("✓ Expert judgment received. Continuing...\n", file=sys.stderr)

                # Auto-call Perplexity after round 5 if not called yet
                if round_num > 5 and not expert_called:
                    print("🔍 Round 5+ without consensus. Auto-calling Perplexity...\n", file=sys.stderr)
                    perplexity_judgment = self.get_perplexity_judgment(claude_final, gemini_final)
                    self.history.append({"round": round_num, "ai": "Perplexity", "response": perplexity_judgment})
                    context += f"\n\n🎯 PERPLEXITY EXPERT JUDGMENT (Auto-called):\n{perplexity_judgment}\n\n"
                    expert_called = True
                    print("✓ Expert judgment received. Continuing...\n", file=sys.stderr)

                continue  # Skip old round 4+ logic

        # Final consensus check
        final_consensus = self.calculate_consensus(claude_final, gemini_final)

        # Trigger Perplexity if needed
        perplexity_judgment = None
        if self.expert_mode or final_consensus < config['debate']['expert_threshold']:
            print("Requesting Perplexity expert judgment...", file=sys.stderr)
            perplexity_judgment = self.get_perplexity_judgment(claude_final, gemini_final)
            self.history.append({"round": "final", "ai": "Perplexity", "response": perplexity_judgment})

        # Compile results
        result = {
            "topic": self.topic,
            "timestamp": datetime.utcnow().isoformat(),
            "rounds": len(self.history) // 2,
            "consensus_score": final_consensus,
            "status": "adopted" if final_consensus >= config['debate']['consensus_threshold'] else "review_required",
            "history": self.history,
            "claude_final_position": claude_final,
            "gemini_final_position": gemini_final,
            "perplexity_judgment": perplexity_judgment
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
                    'perplexity_judgment': result.get('perplexity_judgment'),
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
        f"DEBATE RESULT: {result['topic']}",
        f"{'='*80}\n",
        f"Timestamp: {result['timestamp']}",
        f"Rounds: {result['rounds']}",
    ]

    # Show explicit agreement if available
    if 'consensus_type' in result:
        output.extend([
            f"Agreement Type: {result['consensus_type'].upper()}",
            f"Claude: {result.get('claude_agreement', 'UNKNOWN')}",
            f"Gemini: {result.get('gemini_agreement', 'UNKNOWN')}",
            f"TF-IDF Score (reference): {result['consensus_score']:.2%}",
        ])
    else:
        output.append(f"Consensus: {result['consensus_score']:.2%}")

    output.extend([
        f"Status: {result['status'].upper()}\n",
        f"{'='*80}",
        "\n## CLAUDE'S FINAL POSITION\n",
        result['claude_final_position'],
        f"\n{'='*80}",
        "\n## GEMINI'S FINAL POSITION\n",
        result['gemini_final_position'],
    ])

    if result.get('perplexity_judgment'):
        output.extend([
            f"\n{'='*80}",
            "\n## PERPLEXITY EXPERT JUDGMENT\n",
            result['perplexity_judgment']
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
