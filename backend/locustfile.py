"""
ErgoLab Load Testing with Locust
Run with: locust -f locustfile.py --host=http://localhost:8000

Web UI: http://localhost:8089
"""
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ErgoLabUser(HttpUser):
    """Simulated user for load testing ErgoLab API"""
    
    # Wait 1-3 seconds between tasks
    wait_time = between(1, 3)
    
    # Test credentials
    username = "admin@ergolab.gr"
    password = "admin123"
    
    def on_start(self):
        """Login when user starts"""
        self.token = None
        self.login()
    
    def login(self):
        """Authenticate and store token"""
        response = self.client.post(
            "/api/auth/login",
            data={
                "username": self.username,
                "password": self.password
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.client.headers = {
                "Authorization": f"Bearer {self.token}"
            }
            logger.info("✓ Login successful")
        else:
            logger.error(f"✗ Login failed: {response.status_code}")
    
    @task(5)
    def get_materials(self):
        """Get materials list - high frequency task"""
        page = random.randint(1, 5)
        self.client.get(
            f"/api/materials/?page={page}&per_page=20",
            name="/api/materials/"
        )
    
    @task(3)
    def get_material_detail(self):
        """Get single material - medium frequency"""
        material_id = random.randint(1, 100)
        self.client.get(
            f"/api/materials/{material_id}",
            name="/api/materials/{id}"
        )
    
    @task(4)
    def get_inventory(self):
        """Get inventory for a warehouse - high frequency"""
        warehouse_id = random.randint(1, 5)
        self.client.get(
            f"/api/inventory/warehouse/{warehouse_id}",
            name="/api/inventory/warehouse/{id}"
        )
    
    @task(2)
    def get_projects(self):
        """Get projects list - medium frequency"""
        self.client.get("/api/projects/")
    
    @task(2)
    def get_warehouses(self):
        """Get warehouses list - medium frequency"""
        self.client.get("/api/warehouses/")
    
    @task(1)
    def search_materials(self):
        """Search materials - low frequency"""
        search_terms = ["cable", "pipe", "valve", "pump", "wire", "bolt"]
        term = random.choice(search_terms)
        self.client.get(
            f"/api/materials/?search={term}",
            name="/api/materials/?search={term}"
        )
    
    @task(1)
    def get_low_stock(self):
        """Get low stock items - low frequency"""
        self.client.get("/api/inventory/low-stock")
    
    @task(1)
    def get_dashboard_stats(self):
        """Get dashboard statistics - low frequency"""
        self.client.get("/api/dashboard/stats")
    
    @task(1)
    def create_transaction(self):
        """Create stock transaction - write operation"""
        transaction_data = {
            "warehouse_id": random.randint(1, 5),
            "material_id": random.randint(1, 50),
            "transaction_type": random.choice(["purchase", "sale", "adjustment"]),
            "quantity": random.randint(1, 100),
            "notes": "Load test transaction"
        }
        
        with self.client.post(
            "/api/inventory/transaction",
            json=transaction_data,
            catch_response=True,
            name="/api/inventory/transaction"
        ) as response:
            if response.status_code in [200, 201, 400]:
                # 400 is acceptable (might be invalid data)
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(1)
    def get_transfers(self):
        """Get transfers list - low frequency"""
        self.client.get("/api/transfers/")


class AdminUser(HttpUser):
    """Admin user performing management tasks"""
    
    wait_time = between(3, 8)
    weight = 1  # Less frequent than regular users
    
    username = "admin@ergolab.gr"
    password = "admin123"
    
    def on_start(self):
        response = self.client.post(
            "/api/auth/login",
            data={
                "username": self.username,
                "password": self.password
            }
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.client.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(2)
    def get_reports(self):
        """Generate reports"""
        report_types = ["inventory", "transactions", "overview"]
        report_type = random.choice(report_types)
        self.client.get(
            f"/api/reports/?type={report_type}",
            name="/api/reports/"
        )
    
    @task(1)
    def get_users(self):
        """List users"""
        self.client.get("/api/users/")
    
    @task(1)
    def get_documents(self):
        """List documents"""
        project_id = random.randint(1, 5)
        self.client.get(
            f"/api/documents/?project_id={project_id}",
            name="/api/documents/"
        )


class MobileUser(HttpUser):
    """Mobile app user performing field operations"""
    
    wait_time = between(2, 5)
    weight = 2  # More mobile users than admin
    
    username = "worker@ergolab.gr"
    password = "worker123"
    
    def on_start(self):
        response = self.client.post(
            "/api/auth/login",
            data={
                "username": self.username,
                "password": self.password
            }
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.client.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            # Fallback to admin credentials
            response = self.client.post(
                "/api/auth/login",
                data={
                    "username": "admin@ergolab.gr",
                    "password": "admin123"
                }
            )
            if response.status_code == 200:
                self.token = response.json().get("access_token")
                self.client.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(5)
    def scan_barcode(self):
        """Lookup material by barcode - very frequent"""
        barcode = f"ERG{random.randint(1000, 9999)}"
        self.client.get(
            f"/api/materials/barcode/{barcode}",
            name="/api/materials/barcode/{code}"
        )
    
    @task(3)
    def quick_stock_update(self):
        """Quick stock transaction from mobile"""
        self.client.post(
            "/api/inventory/quick-update",
            json={
                "warehouse_id": random.randint(1, 5),
                "material_id": random.randint(1, 50),
                "quantity_change": random.randint(-10, 10)
            },
            name="/api/inventory/quick-update"
        )
    
    @task(2)
    def sync_data(self):
        """Sync offline data"""
        self.client.get("/api/sync/status")


# Event hooks for logging
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logger.info("=" * 50)
    logger.info("ErgoLab Load Test Started")
    logger.info("=" * 50)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logger.info("=" * 50)
    logger.info("ErgoLab Load Test Completed")
    logger.info("=" * 50)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    if exception:
        logger.error(f"Request failed: {name} - {exception}")
    elif response_time > 1000:  # Log slow requests (>1s)
        logger.warning(f"Slow request: {name} - {response_time}ms")
