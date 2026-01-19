"""
Multi-AI Debate Cloud Function
Vertex AI Agent Builder에서 호출하는 토론 엔드포인트
"""
import os
import json
from typing import Dict, Any
import anthropic
import vertexai
from vertexai.generative_models import GenerativeModel
import functions_framework
from flask import jsonify

# API Keys and Config
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'phsysics')
GCP_LOCATION = os.getenv('GCP_LOCATION', 'us-central1')

# Config
MAX_ROUNDS = int(os.getenv('MAX_ROUNDS', '3'))
CONSENSUS_THRESHOLD = float(os.getenv('CONSENSUS_THRESHOLD', '0.85'))


class QuickDebateEngine:
    """간단한 토론 엔진 (Cloud Function 최적화)"""

    def __init__(self, topic: str):
        self.topic = topic
        self.claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        # Initialize Vertex AI
        vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)
        self.gemini = GenerativeModel('gemini-2.0-flash-exp')

    def get_claude_opinion(self, context: str = "") -> str:
        """Claude 의견"""
        prompt = f"""주제: {self.topic}

{context}

기술적 관점에서 간결하게 의견을 제시하세요 (3-4문장):
- 당신의 입장
- 핵심 근거"""

        try:
            msg = self.claude.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=500,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            return msg.content[0].text
        except Exception as e:
            return f"Claude 응답 오류: {e}"

    def get_gemini_opinion(self, context: str = "") -> str:
        """Gemini 의견"""
        prompt = f"""주제: {self.topic}

{context}

기술적 관점에서 간결하게 의견을 제시하세요 (3-4문장):
- 당신의 입장
- 핵심 근거"""

        try:
            # Vertex AI SDK uses generation_config as a dict
            response = self.gemini.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.7,
                    'max_output_tokens': 500
                }
            )
            return response.text
        except Exception as e:
            return f"Gemini 응답 오류: {e}"

    def calculate_consensus(self, text1: str, text2: str) -> float:
        """간단한 합의도 계산"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # 공통 불용어 제거
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        words1 -= stopwords
        words2 -= stopwords

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def debate(self) -> Dict[str, Any]:
        """토론 실행"""
        context = ""
        claude_final = ""
        gemini_final = ""

        for round_num in range(1, MAX_ROUNDS + 1):
            # Claude 의견
            claude_opinion = self.get_claude_opinion(context)
            context += f"\n\nClaude (Round {round_num}):\n{claude_opinion}"
            claude_final = claude_opinion

            # Gemini 의견
            gemini_opinion = self.get_gemini_opinion(context)
            context += f"\n\nGemini (Round {round_num}):\n{gemini_opinion}"
            gemini_final = gemini_opinion

            # 합의도 계산
            consensus = self.calculate_consensus(claude_final, gemini_final)

            # 충분한 합의 도달?
            if consensus >= CONSENSUS_THRESHOLD:
                break

        final_consensus = self.calculate_consensus(claude_final, gemini_final)

        return {
            "topic": self.topic,
            "rounds": round_num,
            "consensus_score": round(final_consensus, 2),
            "status": "adopted" if final_consensus >= CONSENSUS_THRESHOLD else "review_required",
            "claude_position": claude_final,
            "gemini_position": gemini_final,
            "recommendation": self._generate_recommendation(claude_final, gemini_final, final_consensus)
        }

    def _generate_recommendation(self, claude: str, gemini: str, consensus: float) -> str:
        """최종 추천안 생성"""
        if consensus >= 0.85:
            return f"양측이 높은 합의({consensus:.0%})를 보입니다. 제안된 접근 방식을 채택하는 것을 권장합니다."
        elif consensus >= 0.70:
            return f"중간 수준의 합의({consensus:.0%})입니다. 양측 의견을 검토 후 결정하세요."
        else:
            return f"합의가 낮습니다({consensus:.0%}). 추가 논의가 필요합니다."


@functions_framework.http
def debate(request):
    """
    HTTP 엔드포인트

    Request:
    {
        "topic": "토론 주제"
    }

    Response:
    {
        "fulfillmentResponse": {
            "messages": [{
                "text": {"text": ["토론 결과..."]}
            }]
        }
    }
    """
    # CORS 헤더
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)

    headers = {'Access-Control-Allow-Origin': '*'}

    try:
        # 요청 파싱
        request_json = request.get_json(silent=True)

        # Dialogflow CX webhook 형식 처리
        if request_json and 'sessionInfo' in request_json:
            # Dialogflow CX webhook
            parameters = request_json.get('sessionInfo', {}).get('parameters', {})
            topic = parameters.get('topic', '')

            if not topic:
                # 텍스트에서 추출
                text = request_json.get('text', '')
                topic = text.replace('토론', '').replace('debate', '').strip()
        else:
            # 일반 HTTP 요청
            topic = request_json.get('topic', '') if request_json else ''

        if not topic:
            return jsonify({
                "fulfillmentResponse": {
                    "messages": [{
                        "text": {"text": ["토론 주제를 입력해주세요."]}
                    }]
                }
            }), 200, headers

        # 토론 시작 메시지
        print(f"토론 시작: {topic}")

        # 토론 실행
        engine = QuickDebateEngine(topic)
        result = engine.debate()

        # 응답 포맷팅
        response_text = f"""🤖 Multi-AI 토론 완료!

📊 **토론 주제**: {result['topic']}
**라운드**: {result['rounds']}
**합의도**: {result['consensus_score']:.0%}
**상태**: {"✅ 채택 권장" if result['status'] == 'adopted' else "⚠️ 검토 필요"}

💭 **Claude 의견**:
{result['claude_position'][:300]}...

💭 **Gemini 의견**:
{result['gemini_position'][:300]}...

📝 **추천사항**:
{result['recommendation']}
"""

        # Dialogflow CX 응답 형식
        return jsonify({
            "fulfillmentResponse": {
                "messages": [{
                    "text": {"text": [response_text]}
                }]
            }
        }), 200, headers

    except Exception as e:
        error_msg = f"토론 중 오류 발생: {str(e)}"
        print(error_msg)

        return jsonify({
            "fulfillmentResponse": {
                "messages": [{
                    "text": {"text": [error_msg]}
                }]
            }
        }), 200, headers
