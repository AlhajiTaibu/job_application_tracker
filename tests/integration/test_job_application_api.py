import pytest


class TestJobApplicationApi:

    def test_job_application_api(self, authenticated_client):
        response = authenticated_client.get('/api/v1/job_application/list')
        assert response.status_code == 200