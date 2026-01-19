"""
Vertex AI Search Cloud Function
과거 결정 및 지식 검색
"""
import os
import json
from typing import List, Dict, Any
import functions_framework
from flask import jsonify
from google.cloud import bigquery
import vertexai
from vertexai.language_models import TextEmbeddingModel

# Config
PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'phsysics')
LOCATION = os.getenv('GCP_LOCATION', 'us-central1')
SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.7'))
MAX_RESULTS = int(os.getenv('MAX_RESULTS', '5'))


class VertexSearch:
    """Vertex AI 검색"""

    def __init__(self):
        self.bq_client = bigquery.Client(project=PROJECT_ID)
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        self.embedding_model = TextEmbeddingModel.from_pretrained('textembedding-gecko@003')

    def search(self, query: str) -> List[Dict[str, Any]]:
        """검색 실행"""
        # 쿼리 임베딩 생성
        embeddings = self.embedding_model.get_embeddings([query])
        query_embedding = embeddings[0].values

        # BigQuery 검색
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        sql = f"""
        WITH query_embedding AS (
            SELECT {embedding_str} as embedding
        )
        SELECT
            content,
            metadata,
            ML.DISTANCE(embedding, query_embedding.embedding, 'COSINE') as distance
        FROM
            `{PROJECT_ID}.knowledge_base.embeddings`,
            query_embedding
        WHERE
            ML.DISTANCE(embedding, query_embedding.embedding, 'COSINE') < {1 - SIMILARITY_THRESHOLD}
        ORDER BY
            distance ASC
        LIMIT {MAX_RESULTS}
        """

        try:
            results = []
            query_job = self.bq_client.query(sql)

            for row in query_job:
                results.append({
                    'content': row.content[:200] + "..." if len(row.content) > 200 else row.content,
                    'relevance': round(1 - row.distance, 2),
                    'metadata': json.loads(row.metadata) if isinstance(row.metadata, str) else row.metadata
                })

            return results

        except Exception as e:
            print(f"검색 오류: {e}")
            return []


@functions_framework.http
def search(request):
    """
    HTTP 엔드포인트

    Request:
    {
        "query": "검색어"
    }

    Response:
    {
        "fulfillmentResponse": {
            "messages": [{
                "text": {"text": ["검색 결과..."]}
            }]
        }
    }
    """
    # CORS
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)

    headers = {'Access-Control-Allow-Origin': '*'}

    try:
        request_json = request.get_json(silent=True)

        # Dialogflow CX 형식
        if request_json and 'sessionInfo' in request_json:
            parameters = request_json.get('sessionInfo', {}).get('parameters', {})
            query = parameters.get('query', '')

            if not query:
                text = request_json.get('text', '')
                query = text.replace('검색', '').replace('search', '').strip()
        else:
            query = request_json.get('query', '') if request_json else ''

        if not query:
            return jsonify({
                "fulfillmentResponse": {
                    "messages": [{
                        "text": {"text": ["검색어를 입력해주세요."]}
                    }]
                }
            }), 200, headers

        print(f"검색 시작: {query}")

        # 검색 실행
        searcher = VertexSearch()
        results = searcher.search(query)

        if not results:
            response_text = f"'{query}'에 대한 검색 결과가 없습니다."
        else:
            response_text = f"🔍 '{query}' 검색 결과 ({len(results)}개):\n\n"

            for i, result in enumerate(results, 1):
                response_text += f"**{i}. 관련도 {result['relevance']:.0%}**\n"
                response_text += f"{result['content']}\n\n"

        return jsonify({
            "fulfillmentResponse": {
                "messages": [{
                    "text": {"text": [response_text]}
                }]
            }
        }), 200, headers

    except Exception as e:
        error_msg = f"검색 중 오류: {str(e)}"
        print(error_msg)

        return jsonify({
            "fulfillmentResponse": {
                "messages": [{
                    "text": {"text": [error_msg]}
                }]
            }
        }), 200, headers
