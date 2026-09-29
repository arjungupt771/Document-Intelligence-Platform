from locust import HttpUser, task, between


class DocumentIntelligenceUser(HttpUser):
    wait_time = between(1, 3)
    headers = {"Authorization": "Bearer REPLACE_WITH_TEST_API_KEY"}

    @task(3)
    def health_check(self):
        self.client.get("/health")

    @task(2)
    def ask_question(self):
        self.client.post(
            "/qa/ask",
            json={"query": "What is the total amount on the invoice?"},
            headers=self.headers,
        )

    @task(1)
    def get_analyst_insights(self):
        self.client.get("/analyst/insights", headers=self.headers)