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
import numpy as np
from dotenv import load_dotenv

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
        system_prompt = f"""You are participating in a technical debate.
Topic: {self.topic}

Previous context:
{context}

Be analytical, consider trade-offs, and provide concrete reasoning.
Format your response as:
POSITION: [Your main argument]
REASONING: [Why you believe this]
EVIDENCE: [Supporting facts or examples]

IMPORTANT: If you believe this debate has reached a deadlock and needs a third-party expert (Perplexity) to provide judgment, add [REQUEST_EXPERT] at the very end of your response. Only do this if you genuinely think expert mediation would help reach consensus.
"""

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
        full_prompt = f"""You are participating in a technical debate.
Topic: {self.topic}

Previous context:
{context}

{prompt}

Be analytical, consider trade-offs, and provide concrete reasoning.
Format your response as:
POSITION: [Your main argument]
REASONING: [Why you believe this]
EVIDENCE: [Supporting facts or examples]

IMPORTANT: If you believe this debate has reached a deadlock and needs a third-party expert (Perplexity) to provide judgment, add [REQUEST_EXPERT] at the very end of your response. Only do this if you genuinely think expert mediation would help reach consensus.
"""

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

    def calculate_consensus(self, claude_text: str, gemini_text: str) -> float:
        """Calculate consensus score between two positions"""
        # Simple keyword-based consensus (can be enhanced with embeddings)
        claude_words = set(claude_text.lower().split())
        gemini_words = set(gemini_text.lower().split())

        # Remove common words
        common_stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been'}
        claude_words -= common_stopwords
        gemini_words -= common_stopwords

        if not claude_words or not gemini_words:
            return 0.0

        # Calculate Jaccard similarity
        intersection = len(claude_words & gemini_words)
        union = len(claude_words | gemini_words)

        keyword_similarity = intersection / union if union > 0 else 0.0

        # Weight keyword similarity (in production, add embedding similarity)
        consensus = config['agreement_scoring']['keyword_weight'] * keyword_similarity

        return min(consensus, 1.0)

    def conduct_debate(self) -> Dict[str, Any]:
        """Conduct the multi-round debate"""
        print(f"\n🔥 Starting debate: {self.topic}\n", file=sys.stderr)

        context = ""
        claude_final = ""
        gemini_final = ""

        for round_num in range(1, self.max_rounds + 1):
            print(f"=== Round {round_num}/{self.max_rounds} ===\n", file=sys.stderr)

            if round_num == 1:
                # Round 1: Claude proposes
                print("Claude proposing...", file=sys.stderr)
                prompt = f"Propose a solution or approach for: {self.topic}"
                claude_response = self.get_claude_response(prompt, context)
                self.history.append({"round": round_num, "ai": "Claude", "response": claude_response})
                context += f"\n\nClaude (Round {round_num}):\n{claude_response}"
                claude_final = claude_response

                # Gemini reviews
                print("Gemini reviewing...", file=sys.stderr)
                prompt = f"Review Claude's proposal and provide your analysis. Do you agree? What alternatives exist?"
                gemini_response = self.get_gemini_response(prompt, context)
                self.history.append({"round": round_num, "ai": "Gemini", "response": gemini_response})
                context += f"\n\nGemini (Round {round_num}):\n{gemini_response}"
                gemini_final = gemini_response

            elif round_num == 2:
                # Round 2: Gemini alternative, Claude rebuts
                print("Gemini proposing alternative...", file=sys.stderr)
                prompt = f"Based on the discussion, propose your alternative or refined approach."
                gemini_response = self.get_gemini_response(prompt, context)
                self.history.append({"round": round_num, "ai": "Gemini", "response": gemini_response})
                context += f"\n\nGemini (Round {round_num}):\n{gemini_response}"
                gemini_final = gemini_response

                print("Claude rebutting...", file=sys.stderr)
                prompt = f"Respond to Gemini's alternative. What are the merits and drawbacks?"
                claude_response = self.get_claude_response(prompt, context)
                self.history.append({"round": round_num, "ai": "Claude", "response": claude_response})
                context += f"\n\nClaude (Round {round_num}):\n{claude_response}"
                claude_final = claude_response

            elif round_num == 3:
                # Round 3: Compromise
                print("Seeking compromise...", file=sys.stderr)
                prompt = f"Given the discussion, what's a reasonable compromise or synthesis of ideas?"

                claude_response = self.get_claude_response(prompt, context)
                self.history.append({"round": round_num, "ai": "Claude", "response": claude_response})
                context += f"\n\nClaude (Round {round_num}):\n{claude_response}"
                claude_final = claude_response

                gemini_response = self.get_gemini_response(prompt, context)
                self.history.append({"round": round_num, "ai": "Gemini", "response": gemini_response})
                context += f"\n\nGemini (Round {round_num}):\n{gemini_response}"
                gemini_final = gemini_response

            else:
                # Round 4+: Continue debate, push for consensus
                print(f"Round {round_num}: Deepening discussion...", file=sys.stderr)

                # Alternate who goes first to balance the debate
                if round_num % 2 == 0:
                    # Claude first
                    prompt = f"We're at round {round_num}. Review the entire discussion and either: 1) Find common ground with Gemini's position, or 2) Present new compelling evidence for your stance. Focus on convergence."
                    claude_response = self.get_claude_response(prompt, context)
                    self.history.append({"round": round_num, "ai": "Claude", "response": claude_response})
                    context += f"\n\nClaude (Round {round_num}):\n{claude_response}"
                    claude_final = claude_response

                    prompt = f"Respond to Claude's latest points. Can you find areas of agreement? If not, what critical differences remain?"
                    gemini_response = self.get_gemini_response(prompt, context)
                    self.history.append({"round": round_num, "ai": "Gemini", "response": gemini_response})
                    context += f"\n\nGemini (Round {round_num}):\n{gemini_response}"
                    gemini_final = gemini_response
                else:
                    # Gemini first
                    prompt = f"We're at round {round_num}. Review the entire discussion and either: 1) Find common ground with Claude's position, or 2) Present new compelling evidence for your stance. Focus on convergence."
                    gemini_response = self.get_gemini_response(prompt, context)
                    self.history.append({"round": round_num, "ai": "Gemini", "response": gemini_response})
                    context += f"\n\nGemini (Round {round_num}):\n{gemini_response}"
                    gemini_final = gemini_response

                    prompt = f"Respond to Gemini's latest points. Can you find areas of agreement? If not, what critical differences remain?"
                    claude_response = self.get_claude_response(prompt, context)
                    self.history.append({"round": round_num, "ai": "Claude", "response": claude_response})
                    context += f"\n\nClaude (Round {round_num}):\n{claude_response}"
                    claude_final = claude_response

            # Check if both AIs request expert mediation
            claude_requests_expert = '[REQUEST_EXPERT]' in claude_final
            gemini_requests_expert = '[REQUEST_EXPERT]' in gemini_final

            if claude_requests_expert and gemini_requests_expert:
                print("🚨 Both AIs request expert mediation! Calling Perplexity...\n", file=sys.stderr)
                perplexity_judgment = self.get_perplexity_judgment(claude_final, gemini_final)
                self.history.append({"round": round_num, "ai": "Perplexity", "response": perplexity_judgment})
                print("✓ Expert judgment received. Ending debate.\n", file=sys.stderr)

                # Update finals and break
                final_consensus = self.calculate_consensus(claude_final, gemini_final)
                result = {
                    "topic": self.topic,
                    "timestamp": datetime.utcnow().isoformat(),
                    "rounds": len(self.history) // 2,
                    "consensus_score": final_consensus,
                    "status": "expert_mediation",
                    "history": self.history,
                    "claude_final_position": claude_final,
                    "gemini_final_position": gemini_final,
                    "perplexity_judgment": perplexity_judgment
                }

                # Save to Supabase (if available)
                if self.supabase_client:
                    self.save_to_supabase(result)

                return result
            elif claude_requests_expert or gemini_requests_expert:
                requester = "Claude" if claude_requests_expert else "Gemini"
                print(f"⚠️ {requester} requests expert, but not both. Continuing debate...\n", file=sys.stderr)

            # Calculate consensus
            consensus = self.calculate_consensus(claude_final, gemini_final)
            print(f"Consensus score: {consensus:.2%}\n", file=sys.stderr)

            # Check if consensus reached
            if consensus >= config['debate']['consensus_threshold']:
                print(f"✓ Consensus reached ({consensus:.2%})!\n", file=sys.stderr)
                break

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
        f"Consensus: {result['consensus_score']:.2%}",
        f"Status: {result['status'].upper()}\n",
        f"{'='*80}",
        "\n## CLAUDE'S FINAL POSITION\n",
        result['claude_final_position'],
        f"\n{'='*80}",
        "\n## GEMINI'S FINAL POSITION\n",
        result['gemini_final_position'],
    ]

    if result['perplexity_judgment']:
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
