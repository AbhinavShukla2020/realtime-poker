from locust import HttpUser, between, task


class PokerSpectator(HttpUser):
    wait_time = between(0.05, 0.2)

    def on_start(self):
        self.table_id = "load-test"

    @task
    def read_table(self):
        self.client.get(f"/tables/{self.table_id}", name="/tables/:id")

