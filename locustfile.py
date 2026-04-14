from locust import HttpUser, task, between


class WebsiteUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def status(self):
        self.client.get("/status")

    @task(3)
    def schedule(self):
        self.client.get("/schedule")

    @task(2)
    def broadcast(self):
        self.client.get("/broadcast")  # Mock ws as get


# Run: locust -f locustfile.py --headless -u 10 -r 2 -t 24h --logfile load_test.log
# Assert 95% validation/zero crashes in log
