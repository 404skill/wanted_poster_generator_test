"""
Pytest configuration and fixtures for the Wanted Poster Generator API test suite
"""

import pytest
import requests
import io
from PIL import Image


@pytest.fixture(scope="session")
def base_url():
    """
    Base URL for the API under test
    Default to localhost:8000, can be overridden via environment variable
    """
    return "http://app:8000"


@pytest.fixture(scope="session")
def uploaded_image_id(base_url):
    """
    Fixture that uploads a test image and returns its ID
    Used for tests that need an existing image in the system
    """
    # Create a test image
    img = Image.new('RGB', (100, 100), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    # Upload the image
    files = {'file': ('test_fixture.jpg', img_bytes, 'image/jpeg')}
    response = requests.post(f"{base_url}/images", files=files)
    
    if response.status_code != 201:
        pytest.fail(f"Could not upload test image for fixture: {response.text}")
    
    return response.json()['id']


@pytest.fixture(scope="session")  
def processing_image_id(base_url, uploaded_image_id):
    """
    Fixture that triggers processing on an uploaded image
    Returns an image ID that should be in 'processing' status
    """
    # Trigger processing
    response = requests.post(f"{base_url}/images/{uploaded_image_id}/process")
    
    if response.status_code in [200, 409]:  # 409 if already processing
        return uploaded_image_id
    else:
        pytest.fail(f"Could not trigger processing for fixture: {response.text}")


@pytest.fixture(scope="session")
def completed_image_id(base_url):
    """
    Fixture that returns an image ID that should be completed
    This might need to wait for processing or use a pre-existing completed image
    """
    # Try to find a completed image first
    response = requests.get(f"{base_url}/images?status=completed&limit=1")
    
    if response.status_code == 200:
        images = response.json()
        if images:
            return images[0]['id']
    
    # If no completed image exists, create and process one
    # Create a test image
    img = Image.new('RGB', (100, 100), color='green')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    # Upload the image
    files = {'file': ('test_completed.jpg', img_bytes, 'image/jpeg')}
    upload_response = requests.post(f"{base_url}/images", files=files)
    
    if upload_response.status_code != 201:
        pytest.fail(f"Could not upload image for completed fixture: {upload_response.text}")
    
    image_id = upload_response.json()['id']
    
    # Trigger processing
    process_response = requests.post(f"{base_url}/images/{image_id}/process")
    
    if process_response.status_code not in [200, 409]:
        pytest.fail(f"Could not trigger processing for completed fixture: {process_response.text}")
    
    # Wait a bit for processing (this is a simplified approach)
    import time
    time.sleep(2)
    
    return image_id


@pytest.fixture(scope="session")
def failed_image_id(base_url):
    """
    Fixture that returns an image ID that should be in failed status
    This might require a pre-existing failed image or simulation
    """
    # Try to find a failed image first
    response = requests.get(f"{base_url}/images?status=failed&limit=1")
    
    if response.status_code == 200:
        images = response.json()
        if images:
            return images[0]['id']
    
    # If no failed image exists, we'll skip tests that need it
    # In a real scenario, you might create a corrupted image or simulate failure
    pytest.fail("No failed images available for testing") 
