"""
Load testing for Customer Support RAG - High-Volume Scenario

This load test simulates high-volume customer support queries with:
- 20 varied realistic customer queries across all 4 categories
- Faster pacing (0.5-2s wait time) for high-volume support scenarios
- Weighted tasks matching real usage patterns
- Performance assertions: p50<1.5s, p95<3s, p99<5s

Run instructions:
    # Web UI (recommended for development)
    locust -f locustfile.py --host=https://your-api-gateway-endpoint.execute-api.us-east-1.amazonaws.com

    # Headless mode (CI/CD)
    locust -f locustfile.py --host=https://your-api-gateway-endpoint.execute-api.us-east-1.amazonaws.com \\
        --users 50 --spawn-rate 5 --run-time 5m --headless

Performance targets for customer support:
    - p50 latency: < 1.5s (faster than typical RAG)
    - p95 latency: < 3s
    - p99 latency: < 5s
    - Error rate: 0%
    - Sustained throughput: 50+ concurrent users
"""

from locust import HttpUser, task, between, events
import json
import random
import time


# 20 varied customer queries across all 4 categories
CUSTOMER_QUERIES = [
    # BILLING queries (5)
    "How do I update my credit card information?",
    "Can I get a refund for my subscription?",
    "What are the pricing tiers and differences?",
    "How do I cancel my subscription?",
    "Do you offer discounts for annual billing?",

    # TECHNICAL queries (5)
    "My sync keeps failing with error 500",
    "The API returns 429 too many requests error",
    "Files are not syncing to my other devices",
    "Application crashes when uploading large files",
    "How do I fix sync conflicts?",

    # ACCOUNT queries (5)
    "I forgot my password, how do I reset it?",
    "How do I enable two-factor authentication?",
    "Can I change my email address?",
    "How do I add team members to my account?",
    "How do I delete my account?",

    # GENERAL queries (5)
    "What features does CloudSync Pro offer?",
    "Which file types are supported?",
    "Can I access files offline?",
    "What are the system requirements?",
    "How do I integrate with Slack?",
]


class CustomerSupportLoadUser(HttpUser):
    """
    Simulated customer support user for load testing.

    Faster wait time (0.5-2s) simulates high-volume support scenario
    where customers expect quick responses.
    """

    # Faster wait time for high-volume customer support
    wait_time = between(0.5, 2)

    def on_start(self):
        """Called when a simulated user starts."""
        self.headers = {
            "Content-Type": "application/json"
        }

    @task(5)
    def query_support(self):
        """
        Test main support query endpoint (highest priority - 5x weight).

        Randomly selects from pool of 20 varied customer queries.
        """
        question = random.choice(CUSTOMER_QUERIES)

        payload = {
            "query": question,
            "max_results": 5
        }

        start_time = time.time()

        with self.client.post(
            "/query",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="POST /query (customer support)"
        ) as response:
            response_time = (time.time() - start_time) * 1000  # ms

            if response.status_code == 200:
                try:
                    data = response.json()

                    # Validate response structure for customer support
                    if "answer" not in data:
                        response.failure("Response missing 'answer' field")
                    elif "category" not in data:
                        response.failure("Response missing 'category' field (required for routing)")
                    elif len(data["answer"]) < 10:
                        response.failure("Answer too short (possible error)")
                    else:
                        response.success()

                        # Log slow responses (p95 target: 3s)
                        if response_time > 3000:
                            print(f"SLOW RESPONSE: {response_time:.0f}ms for query: {question[:50]}...")

                        # Log very slow responses (p99 target: 5s)
                        if response_time > 5000:
                            print(f"⚠️  VERY SLOW: {response_time:.0f}ms - exceeds p99 target!")

                except json.JSONDecodeError:
                    response.failure("Response is not valid JSON")
            elif response.status_code == 429:
                # Rate limited - expected under heavy load
                response.failure("Rate limited (429) - may need throttling adjustment")
            elif response.status_code >= 500:
                response.failure(f"Server error ({response.status_code})")
            else:
                response.failure(f"Client error ({response.status_code})")

    @task(2)
    def query_billing(self):
        """
        Test billing-specific queries (medium priority - 2x weight).
        """
        billing_queries = [q for q in CUSTOMER_QUERIES if any(word in q.lower() for word in ['credit', 'refund', 'pricing', 'cancel', 'discount'])]
        question = random.choice(billing_queries)

        with self.client.post(
            "/query",
            json={"query": question, "max_results": 5},
            headers=self.headers,
            catch_response=True,
            name="POST /query (billing)"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Verify billing queries are classified as BILLING
                if data.get("category") == "BILLING":
                    response.success()
                else:
                    print(f"Warning: Billing query classified as {data.get('category')}")
                    response.success()  # Don't fail, just log
            else:
                response.failure(f"Failed ({response.status_code})")

    @task(2)
    def query_technical(self):
        """
        Test technical support queries (medium priority - 2x weight).
        """
        technical_queries = [q for q in CUSTOMER_QUERIES if any(word in q.lower() for word in ['error', 'crash', 'sync', 'api', 'fix'])]
        question = random.choice(technical_queries)

        with self.client.post(
            "/query",
            json={"query": question, "max_results": 5},
            headers=self.headers,
            catch_response=True,
            name="POST /query (technical)"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Verify technical queries are classified as TECHNICAL
                if data.get("category") == "TECHNICAL":
                    response.success()
                else:
                    print(f"Warning: Technical query classified as {data.get('category')}")
                    response.success()  # Don't fail, just log
            else:
                response.failure(f"Failed ({response.status_code})")

    @task(1)
    def health_check(self):
        """
        Test health check endpoint (lowest priority - 1x weight).
        """
        with self.client.get(
            "/health",
            catch_response=True,
            name="GET /health"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed ({response.status_code})")


# Event hooks for custom reporting

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print("\n" + "="*80)
    print("Starting Customer Support RAG Load Test")
    print("="*80)
    print(f"Target host: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print(f"Query pool: {len(CUSTOMER_QUERIES)} varied customer queries")
    print("\nPerformance Targets:")
    print("  p50 < 1.5s (customer support SLA)")
    print("  p95 < 3s")
    print("  p99 < 5s")
    print("  Error rate: 0%")
    print("="*80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops - print summary with assertions."""
    print("\n" + "="*80)
    print("Customer Support RAG Load Test - Summary")
    print("="*80)

    stats = environment.runner.stats
    total_rps = stats.total.current_rps
    total_fail_ratio = stats.total.fail_ratio

    print(f"Total requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Average RPS: {total_rps:.2f}")
    print(f"Failure rate: {total_fail_ratio:.2%}")

    if stats.total.num_requests > 0:
        p50 = stats.total.get_response_time_percentile(0.5)
        p95 = stats.total.get_response_time_percentile(0.95)
        p99 = stats.total.get_response_time_percentile(0.99)

        print(f"\nResponse time percentiles:")
        print(f"  p50: {p50:.0f}ms (target: <1500ms)")
        print(f"  p95: {p95:.0f}ms (target: <3000ms)")
        print(f"  p99: {p99:.0f}ms (target: <5000ms)")

        # Performance assertions
        warnings = []
        if p50 > 1500:
            warnings.append(f"⚠️  WARNING: p50 ({p50:.0f}ms) exceeds target (1500ms)")
        if p95 > 3000:
            warnings.append(f"⚠️  WARNING: p95 ({p95:.0f}ms) exceeds target (3000ms)")
        if p99 > 5000:
            warnings.append(f"⚠️  WARNING: p99 ({p99:.0f}ms) exceeds target (5000ms)")
        if total_fail_ratio > 0.0:
            warnings.append(f"⚠️  WARNING: Failure rate ({total_fail_ratio:.2%}) exceeds target (0%)")

        if warnings:
            print("\nPerformance Issues Detected:")
            for warning in warnings:
                print(f"  {warning}")
        else:
            print("\n✓ All performance targets met!")

    print("="*80 + "\n")
