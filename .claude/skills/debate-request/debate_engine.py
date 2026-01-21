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

        # Assign expert personas based on topic
        self.claude_persona, self.gemini_persona = self.assign_personas(topic)

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

    def assign_personas(self, topic: str) -> Tuple[str, str]:
        """Assign expert personas based on the topic"""
        # Use Claude to automatically assign appropriate expert roles
        try:
            message = self.claude_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1000,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": f"""주제: {topic}

이 주제에 대해 토론할 두 명의 전문가 역할을 정의해주세요.
두 전문가는 서로 다른 관점이나 전문 분야를 가져야 하며, 건설적인 합의를 도출할 수 있어야 합니다.

다음 형식으로 답변해주세요:
EXPERT_A: [역할 설명]
EXPERT_B: [역할 설명]

예시:
EXPERT_A: 클라우드 아키텍트 - 확장성과 비용 최적화에 중점
EXPERT_B: 보안 전문가 - 데이터 보호와 컴플라이언스에 중점"""
                }]
            )

            response_text = message.content[0].text

            # Parse personas
            claude_persona = "기술 전문가"  # default
            gemini_persona = "시스템 설계자"  # default

            for line in response_text.split('\n'):
                if 'EXPERT_A:' in line:
                    claude_persona = line.split('EXPERT_A:')[1].strip()
                elif 'EXPERT_B:' in line:
                    gemini_persona = line.split('EXPERT_B:')[1].strip()

            print(f"\n👤 전문가 역할 배정:", file=sys.stderr)
            print(f"   Claude: {claude_persona}", file=sys.stderr)
            print(f"   Gemini: {gemini_persona}\n", file=sys.stderr)

            return claude_persona, gemini_persona

        except Exception as e:
            print(f"⚠ 페르소나 배정 실패: {e}, 기본값 사용", file=sys.stderr)
            return "기술 전문가", "시스템 설계자"

    def get_claude_response(self, prompt: str, context: str = "", perplexity_feedback: str = "") -> str:
        """Get response from Claude with assigned persona"""
        feedback_section = f"\n\n**Perplexity 피드백**:\n{perplexity_feedback}" if perplexity_feedback else ""

        system_prompt = f"""당신의 역할: **{self.claude_persona}**

주제: {self.topic}

이전 대화 내용:
{context}{feedback_section}

**목표**: 3라운드 내에 상대 전문가({self.gemini_persona})와 **실용적인 합의안**을 도출하는 것입니다.

**중요 원칙**:
1. 당신의 전문 분야 관점에서 의견 제시
2. 상대 전문가의 관점을 존중하고 절충점 찾기
3. 구체적이고 실행 가능한 제안 작성
4. 간결하게 작성 (500-800자)
5. **반드시 한글로 답변**

**반드시 한글로 답변해주세요.**"""

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

    def get_gemini_response(self, prompt: str, context: str = "", perplexity_feedback: str = "") -> str:
        """Get response from Gemini with assigned persona"""
        feedback_section = f"\n\n**Perplexity 피드백**:\n{perplexity_feedback}" if perplexity_feedback else ""

        full_prompt = f"""당신의 역할: **{self.gemini_persona}**

주제: {self.topic}

이전 대화 내용:
{context}{feedback_section}

{prompt}

**목표**: 3라운드 내에 상대 전문가({self.claude_persona})와 **실용적인 합의안**을 도출하는 것입니다.

**중요 원칙**:
1. 당신의 전문 분야 관점에서 의견 제시
2. 상대 전문가의 관점을 존중하고 절충점 찾기
3. 구체적이고 실행 가능한 제안 작성
4. 간결하게 작성 (500-800자)
5. **반드시 한글로 답변**

**반드시 한글로 답변해주세요.**"""

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

    def get_perplexity_judgment(self, claude_pos: str, gemini_pos: str) -> Dict[str, Any]:
        """Get judgment from Perplexity on whether consensus is acceptable"""
        if not PERPLEXITY_API_KEY or not config['participants']['perplexity']['enabled']:
            return {"approved": True, "feedback": "Perplexity not available"}

        prompt = f"""당신은 **합의안 검증자**입니다. 두 전문가의 제안을 검토하고 **승인 여부**를 판단하세요.

주제: {self.topic}

**전문가 A ({self.claude_persona})의 제안**:
{claude_pos}

**전문가 B ({self.gemini_persona})의 제안**:
{gemini_pos}

**평가 기준**:
1. 두 제안이 실질적으로 합의에 도달했는가?
2. 제안이 구체적이고 실행 가능한가?
3. 핵심 쟁점에 대한 명확한 결론이 있는가?

**답변 형식** (반드시 이 형식으로):
DECISION: [APPROVE / REJECT]
REASON: [1-2문장으로 이유 설명]

APPROVE인 경우: 왜 좋은 합의안인지
REJECT인 경우: 무엇이 부족하고 어떻게 개선해야 하는지

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
            result_text = response.json()['choices'][0]['message']['content']

            # Parse decision
            approved = False
            feedback = result_text

            for line in result_text.split('\n'):
                if 'DECISION:' in line:
                    if 'APPROVE' in line.upper():
                        approved = True
                elif 'REASON:' in line:
                    feedback = line.split('REASON:')[1].strip()

            return {
                "approved": approved,
                "feedback": feedback,
                "full_response": result_text
            }

        except Exception as e:
            print(f"⚠ Perplexity 판정 실패: {e}", file=sys.stderr)
            return {"approved": True, "feedback": f"Error: {e}"}

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
        """Conduct debate with Perplexity approval cycles"""
        print(f"\n🎯 전문가 토론 시작: {self.topic}\n", file=sys.stderr)
        print(f"목표: 3라운드 내 합의 도달 → Perplexity 승인\n", file=sys.stderr)

        MAX_CYCLES = 3
        ROUNDS_PER_CYCLE = 3

        context = ""
        claude_final = ""
        gemini_final = ""
        perplexity_feedback = ""
        total_rounds = 0
        approved = False

        for cycle in range(1, MAX_CYCLES + 1):
            print(f"\n{'='*80}", file=sys.stderr)
            print(f"📍 Cycle {cycle}/{MAX_CYCLES}", file=sys.stderr)
            print(f"{'='*80}\n", file=sys.stderr)

            if cycle > 1:
                print(f"⚠️  Perplexity 피드백: {perplexity_feedback}\n", file=sys.stderr)

            # 3 rounds of discussion per cycle
            for round_num in range(1, ROUNDS_PER_CYCLE + 1):
                total_rounds += 1
                print(f"--- Round {round_num}/3 (Cycle {cycle}) ---\n", file=sys.stderr)

                # Prompt
                if total_rounds == 1:
                    prompt = "당신의 전문 분야 관점에서 이 주제에 대한 의견을 제시해주세요."
                else:
                    prompt = "상대 전문가의 의견을 고려하여 합의 가능한 제안을 작성해주세요."

                # Claude's turn
                print(f"🔵 Claude ({self.claude_persona})...", file=sys.stderr)
                claude_response = self.get_claude_response(prompt, context, perplexity_feedback)
                self.history.append({"cycle": cycle, "round": round_num, "ai": "Claude", "response": claude_response})
                context += f"\n\nClaude (Cycle {cycle}, Round {round_num}):\n{claude_response}"
                claude_final = claude_response

                # Gemini's turn
                print(f"🟢 Gemini ({self.gemini_persona})...\n", file=sys.stderr)
                gemini_response = self.get_gemini_response(prompt, context, perplexity_feedback)
                self.history.append({"cycle": cycle, "round": round_num, "ai": "Gemini", "response": gemini_response})
                context += f"\n\nGemini (Cycle {cycle}, Round {round_num}):\n{gemini_response}"
                gemini_final = gemini_response

            # Perplexity judgment after 3 rounds
            print(f"\n🎯 Perplexity 판정 중...", file=sys.stderr)
            judgment = self.get_perplexity_judgment(claude_final, gemini_final)

            self.history.append({
                "cycle": cycle,
                "round": "judgment",
                "ai": "Perplexity",
                "response": judgment["full_response"]
            })

            if judgment["approved"]:
                print(f"✅ Perplexity 승인! Cycle {cycle}에서 합의 완료.\n", file=sys.stderr)
                approved = True
                break
            else:
                print(f"❌ Perplexity 거절", file=sys.stderr)
                print(f"   이유: {judgment['feedback']}\n", file=sys.stderr)
                perplexity_feedback = judgment["feedback"]

                if cycle < MAX_CYCLES:
                    print(f"🔄 Cycle {cycle + 1}으로 재시도...\n", file=sys.stderr)

        # Calculate similarity score for reference
        consensus_score = self.calculate_consensus(claude_final, gemini_final)

        # Compile results
        status = "approved" if approved else "max_cycles_reached"
        result = {
            "topic": self.topic,
            "timestamp": datetime.utcnow().isoformat(),
            "cycles": cycle,
            "total_rounds": total_rounds,
            "consensus_score": consensus_score,
            "status": status,
            "perplexity_approved": approved,
            "history": self.history,
            "claude_persona": self.claude_persona,
            "gemini_persona": self.gemini_persona,
            "claude_final_position": claude_final,
            "gemini_final_position": gemini_final,
            "perplexity_final_judgment": judgment["full_response"]
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
                'rounds': result['total_rounds'],
                'metadata': {
                    'timestamp': result['timestamp'],
                    'status': result['status'],
                    'cycles': result['cycles'],
                    'perplexity_approved': result['perplexity_approved'],
                    'claude_persona': result['claude_persona'],
                    'gemini_persona': result['gemini_persona'],
                    'rounds_detail': result['history'],
                    'perplexity_judgment': result.get('perplexity_final_judgment'),
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
    approval_status = "✅ 승인됨" if result['perplexity_approved'] else "⚠️ 최대 사이클 도달"

    output = [
        f"\n{'='*80}",
        f"🎯 전문가 토론 결과: {result['topic']}",
        f"{'='*80}\n",
        f"Timestamp: {result['timestamp']}",
        f"Cycles: {result['cycles']}",
        f"Total Rounds: {result['total_rounds']}",
        f"Similarity Score: {result['consensus_score']:.2%}",
        f"Perplexity 판정: {approval_status}",
        f"Status: {result['status'].upper()}\n",
        f"{'='*80}",
        f"\n## 👤 전문가 A: {result['claude_persona']}\n",
        result['claude_final_position'],
        f"\n{'='*80}",
        f"\n## 👤 전문가 B: {result['gemini_persona']}\n",
        result['gemini_final_position'],
    ]

    if result.get('perplexity_final_judgment'):
        output.extend([
            f"\n{'='*80}",
            "\n## 🎯 Perplexity 최종 판정\n",
            result['perplexity_final_judgment']
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
