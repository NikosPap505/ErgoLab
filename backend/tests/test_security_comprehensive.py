import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestSecurity:
    def test_sql_injection_protection(self):
        """Test SQL injection in category filter"""
        response = client.get(
            "/api/materials/",
            params={"category": "'; DROP TABLE materials; --"}
        )
        assert response.status_code in [400, 422]  # Should be rejected
    
    def test_xss_protection(self):
        """Test XSS in material name"""
        response = client.post(
            "/api/materials/",
            json={
                "name": "<script>alert('XSS')</script>",
                "sku": "TEST-001",
                "unit": "kg"
            },
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code in [400, 422]  # Should be rejected
    
    def test_negative_price_validation(self):
        """Test negative unit price"""
        response = client.post(
            "/api/materials/",
            json={
                "name": "Test Material",
                "sku": "TEST-002",
                "unit": "kg",
                "unit_price": -10.50
            },
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 422
        assert "negative" in response.json()["detail"][0]["msg"].lower()
    
    def test_batch_qr_limit(self):
        """Test batch QR generation limit"""
        # Generate 101 IDs
        ids = ",".join(str(i) for i in range(1, 102))
        response = client.get(
            f"/api/materials/qr/batch?material_ids={ids}",
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 400
        assert "exceeds maximum" in response.json()["detail"].lower()
    
    def test_rate_limiting(self):
        """Test login rate limiting"""
        # Try 6 login attempts
        for i in range(6):
            response = client.post(
                "/api/auth/login",
                data={"username": "test@test.com", "password": "wrong"}
            )
            if i < 5:
                assert response.status_code == 401
            else:
                assert response.status_code == 429  # Rate limited
