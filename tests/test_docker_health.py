import pytest
import requests
import yaml
import time
from urllib.parse import urlparse

def get_services_from_compose():
    """Reads docker-compose.yml and extracts service healthcheck URLs."""
    services = []
    try:
        with open("docker-compose.yml", "r", encoding="utf-8") as f:
            compose_config = yaml.safe_load(f)
        
        for service_name, service_config in compose_config.get("services", {}).items():
            if "healthcheck" in service_config and "test" in service_config["healthcheck"]:
                test_command = service_config["healthcheck"]["test"]
                url = ""
                if "curl" in str(test_command):
                    # Extract URL from curl command
                    for item in test_command:
                        if "http://" in item:
                            url = item
                            break
                
                if url:
                    # Replace service name with localhost for local testing
                    parsed_url = urlparse(url)
                    port = parsed_url.port
                    if port:
                        local_url = f"http://localhost:{port}{parsed_url.path}"
                        services.append({"name": service_name, "url": local_url})

    except FileNotFoundError:
        pytest.fail("docker-compose.yml not found in the root directory.")
    except Exception as e:
        pytest.fail(f"Error reading or parsing docker-compose.yml: {e}")
        
    return services

@pytest.mark.parametrize("service", get_services_from_compose())
def test_service_health(service):
    """Tests the health of a single service."""
    service_name = service["name"]
    url = service["url"]
    
    print(f"Checking health for service: {service_name} at {url}")
    
    max_retries = 15
    retry_delay = 10  # seconds
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"Service {service_name} is healthy.")
                assert True
                return
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed for {service_name}: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)

    pytest.fail(f"Service {service_name} ({url}) is not healthy after {max_retries} attempts.")

if __name__ == "__main__":
    pytest.main([__file__])
