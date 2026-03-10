"""
RAG evaluation using LLM-as-judge pattern

Evaluates RAG answer quality for customer support queries.
"""

import pytest
import json


def evaluate_rag_answer(client, question: str, context: list, answer: str) -> dict:
    """
    Evaluate RAG answer quality using Claude as a judge.
    """
    context_text = "\n\n".join([chunk.get('content', str(chunk)) if isinstance(chunk, dict) else chunk for chunk in context])

    judge_prompt = f"""You are evaluating a customer support RAG system's answer quality.

QUESTION:
{question}

RETRIEVED CONTEXT:
{context_text}

RAG SYSTEM ANSWER:
{answer}

Evaluate the answer:
1. FAITHFULNESS: Is the answer fully supported by the context? (yes/no + explanation)
2. CORRECTNESS: Does the answer correctly address the customer's question? (yes/no + explanation)
3. OVERALL SCORE: Assign a score from 0.0 to 1.0 (explanation + score)

Respond ONLY with valid JSON:
{{
  "faithfulness": "yes or no",
  "faithfulness_explanation": "your reasoning",
  "correctness": "yes or no",
  "correctness_explanation": "your reasoning",
  "overall_score": 0.85,
  "overall_explanation": "your reasoning"
}}"""

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [{"role": "user", "content": judge_prompt}],
        "max_tokens": 1000,
        "temperature": 0.0
    }

    response = client.invoke_model(
        modelId='anthropic.claude-sonnet-4-5-20250929-v1:0',
        contentType='application/json',
        accept='application/json',
        body=json.dumps(request_body)
    )

    response_body = json.loads(response['body'].read())
    judge_text = response_body['content'][0]['text'].strip()

    # Clean markdown formatting
    if judge_text.startswith('```json'):
        judge_text = judge_text[7:]
    if judge_text.startswith('```'):
        judge_text = judge_text[3:]
    if judge_text.endswith('```'):
        judge_text = judge_text[:-3]
    judge_text = judge_text.strip()

    return json.loads(judge_text)


@pytest.mark.integration
def test_billing_query_evaluation(real_bedrock_client):
    """Test RAG evaluation for billing query"""

    question = "How do I cancel my subscription?"
    context = [
        "To cancel your subscription: Go to Settings > Billing, click 'Cancel Subscription', confirm cancellation. You retain access until the end of your billing period."
    ]
    answer = "You can cancel your subscription by going to Settings > Billing and clicking 'Cancel Subscription'. You'll keep access until your current billing period ends."

    evaluation = evaluate_rag_answer(real_bedrock_client, question, context, answer)

    assert evaluation['faithfulness'] == 'yes'
    assert evaluation['correctness'] == 'yes'
    assert evaluation['overall_score'] >= 0.8


@pytest.mark.integration
def test_technical_query_evaluation(real_bedrock_client):
    """Test RAG evaluation for technical query"""

    question = "My API returns 429 error"
    context = [
        "Error 429 Too Many Requests indicates you've exceeded your API rate limit. Check X-RateLimit-Remaining header. Implement exponential backoff and consider upgrading your plan."
    ]
    answer = "Error 429 means you've hit your API rate limit. Check the X-RateLimit-Remaining header to see how many requests you have left. Use exponential backoff when retrying, and consider upgrading your plan for higher limits."

    evaluation = evaluate_rag_answer(real_bedrock_client, question, context, answer)

    assert evaluation['faithfulness'] == 'yes'
    assert evaluation['correctness'] == 'yes'
    assert evaluation['overall_score'] >= 0.8
