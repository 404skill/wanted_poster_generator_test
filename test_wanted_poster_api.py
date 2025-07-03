"""
Comprehensive test suite for the Wanted Poster Generator API
Tests all functional requirements from spec.md

Each test class corresponds to a task from the specification:
- TestTask1HealthCheck: Health endpoint validation
- TestTask2ImageUpload: Image upload functionality 
- TestTask3StatusCheck: Status checking endpoint
- TestTask4ImageDownload: Image download endpoint
- TestTask5ProcessTrigger: Processing trigger endpoint
- TestTask6BackgroundWorker: Background worker behavior
- TestTask7AdminListView: Admin list view with pagination
- TestTask8SignedUrl: Signed URL generation (optional)
"""

import pytest
import requests
import json
import uuid
import io
from PIL import Image
import time


class TestTask1HealthCheck:
    """Test Task 1: Initialize Project - Health Check Endpoint"""

    def test_health_check_returns_200_with_correct_json_response(self, base_url):
        """Test that GET /health returns 200 OK with expected JSON structure"""
        response = requests.get(f"{base_url}/health")
        
        assert response.status_code == 200, (
            f"Health check endpoint should return 200 OK but got {response.status_code}. "
            f"Response: {response.text}"
        )
        
        assert response.headers.get('content-type', '').startswith('application/json'), (
            f"Health check should return JSON content type but got '{response.headers.get('content-type')}'"
        )
        
        json_data = response.json()
        assert json_data == {"status": "OK"}, (
            f"Health check should return exactly {{'status': 'OK'}} but got {json_data}"
        )


class TestTask2ImageUpload:
    """Test Task 2: Define Image Model and POST /images Route"""

    def create_test_image(self, format='JPEG', size=(100, 100), file_size_mb=None):
        """Helper to create test images of various formats and sizes"""
        img = Image.new('RGB', size, color='red')
        img_bytes = io.BytesIO()
        
        if file_size_mb:
            # Create image of specific size for testing file size limits
            target_size = file_size_mb * 1024 * 1024
            quality = 95
            while True:
                img_bytes.seek(0)
                img_bytes.truncate()
                img.save(img_bytes, format=format, quality=quality)
                if img_bytes.tell() >= target_size:
                    break
                quality -= 1
                if quality < 1:
                    # If we can't reach target size, create a larger image
                    new_size = (size[0] * 2, size[1] * 2)
                    img = Image.new('RGB', new_size, color='red')
                    size = new_size
                    quality = 95
        else:
            img.save(img_bytes, format=format)
        
        img_bytes.seek(0)
        return img_bytes

    def test_successful_image_upload_returns_201_with_uuid_and_pending_status(self, base_url):
        """Test that valid image upload returns 201 Created with UUID and pending status"""
        test_image = self.create_test_image()
        files = {'file': ('test.jpg', test_image, 'image/jpeg')}
        
        response = requests.post(f"{base_url}/images", files=files)
        
        assert response.status_code == 201, (
            f"Valid image upload should return 201 Created but got {response.status_code}. "
            f"Response: {response.text}"
        )
        
        json_data = response.json()
        assert 'id' in json_data, f"Response should contain 'id' field but got {json_data}"
        assert 'status' in json_data, f"Response should contain 'status' field but got {json_data}"
        
        # Validate UUID format
        try:
            uuid.UUID(json_data['id'])
        except ValueError:
            pytest.fail(f"Response 'id' should be a valid UUID but got '{json_data['id']}'")
        
        assert json_data['status'] == 'pending', (
            f"Response status should be 'pending' but got '{json_data['status']}'"
        )

    def test_upload_jpeg_image_successfully_accepted(self, base_url):
        """Test that JPEG images are accepted and processed correctly"""
        test_image = self.create_test_image(format='JPEG')
        files = {'file': ('test.jpg', test_image, 'image/jpeg')}
        
        response = requests.post(f"{base_url}/images", files=files)
        
        assert response.status_code == 201, (
            f"JPEG image upload should be accepted but got {response.status_code}. "
            f"Response: {response.text}"
        )

    def test_upload_png_image_successfully_accepted(self, base_url):
        """Test that PNG images are accepted and processed correctly"""
        test_image = self.create_test_image(format='PNG')
        files = {'file': ('test.png', test_image, 'image/png')}
        
        response = requests.post(f"{base_url}/images", files=files)
        
        assert response.status_code == 201, (
            f"PNG image upload should be accepted but got {response.status_code}. "
            f"Response: {response.text}"
        )

    def test_upload_without_file_returns_400_bad_request(self, base_url):
        """Test that request without file returns 400 Bad Request"""
        response = requests.post(f"{base_url}/images")
        
        assert response.status_code == 400, (
            f"Request without file should return 400 Bad Request but got {response.status_code}. "
            f"Response: {response.text}"
        )
        
        json_data = response.json()
        assert 'error' in json_data, f"Error response should contain 'error' field but got {json_data}"
        assert 'no file provided' in json_data['error'].lower(), (
            f"Error message should mention missing file but got '{json_data['error']}'"
        )

    def test_upload_unsupported_file_type_returns_415_unsupported_media_type(self, base_url):
        """Test that unsupported file types return 415 Unsupported Media Type or 400 Bad Request"""
        # Create a text file instead of image
        text_content = io.BytesIO(b"This is not an image file")
        files = {'file': ('test.txt', text_content, 'text/plain')}
        
        response = requests.post(f"{base_url}/images", files=files)
        
        assert response.status_code in [400, 415], (
            f"Unsupported file type should return 400 Bad Request or 415 Unsupported Media Type "
            f"but got {response.status_code}. Response: {response.text}"
        )
        
        json_data = response.json()
        assert 'error' in json_data, f"Error response should contain 'error' field but got {json_data}"
        assert any(keyword in json_data['error'].lower() for keyword in ['invalid', 'unsupported', 'type']), (
            f"Error message should mention invalid file type but got '{json_data['error']}'"
        )

    def test_upload_file_exceeding_5mb_returns_413_payload_too_large(self, base_url):
        """Test that files exceeding 5MB return 413 Payload Too Large"""
        # Create a 6MB image (larger than 5MB limit)
        large_image = self.create_test_image(file_size_mb=6)
        files = {'file': ('large_test.jpg', large_image, 'image/jpeg')}
        
        response = requests.post(f"{base_url}/images", files=files)
        
        assert response.status_code == 413, (
            f"File exceeding 5MB should return 413 Payload Too Large but got {response.status_code}. "
            f"Response: {response.text}"
        )
        
        json_data = response.json()
        assert 'error' in json_data, f"Error response should contain 'error' field but got {json_data}"
        assert '5mb' in json_data['error'].lower() or '5 mb' in json_data['error'].lower(), (
            f"Error message should mention 5MB limit but got '{json_data['error']}'"
        )


class TestTask3StatusCheck:
    """Test Task 3: GET /images/:id/status – Check Processing Status"""

    def test_valid_uuid_returns_image_status_with_timestamps(self, base_url, uploaded_image_id):
        """Test that valid UUID returns current image status and timestamps"""
        response = requests.get(f"{base_url}/images/{uploaded_image_id}/status")
        
        assert response.status_code == 200, (
            f"Valid UUID status check should return 200 OK but got {response.status_code}. "
            f"Response: {response.text}"
        )
        
        json_data = response.json()
        required_fields = ['id', 'status', 'createdAt']
        for field in required_fields:
            assert field in json_data, f"Response should contain '{field}' field but got {json_data}"
        
        assert json_data['id'] == uploaded_image_id, (
            f"Response ID should match requested ID '{uploaded_image_id}' but got '{json_data['id']}'"
        )
        
        valid_statuses = ['pending', 'processing', 'completed', 'failed']
        assert json_data['status'] in valid_statuses, (
            f"Status should be one of {valid_statuses} but got '{json_data['status']}'"
        )
        
        # Validate ISO timestamp format
        assert 'T' in json_data['createdAt'] and 'Z' in json_data['createdAt'], (
            f"createdAt should be ISO timestamp but got '{json_data['createdAt']}'"
        )

    def test_invalid_uuid_format_returns_400_bad_request(self, base_url):
        """Test that invalid UUID format returns 400 Bad Request"""
        invalid_uuid = "not-a-valid-uuid"
        response = requests.get(f"{base_url}/images/{invalid_uuid}/status")
        
        assert response.status_code == 400, (
            f"Invalid UUID should return 400 Bad Request but got {response.status_code}. "
            f"Response: {response.text}"
        )
        
        json_data = response.json()
        assert 'error' in json_data, f"Error response should contain 'error' field but got {json_data}"
        assert 'uuid' in json_data['error'].lower(), (
            f"Error message should mention UUID validation but got '{json_data['error']}'"
        )

    def test_nonexistent_image_id_returns_404_not_found(self, base_url):
        """Test that non-existent image ID returns 404 Not Found"""
        nonexistent_uuid = str(uuid.uuid4())
        response = requests.get(f"{base_url}/images/{nonexistent_uuid}/status")
        
        assert response.status_code == 404, (
            f"Non-existent image ID should return 404 Not Found but got {response.status_code}. "
            f"Response: {response.text}"
        )
        
        json_data = response.json()
        assert 'error' in json_data, f"Error response should contain 'error' field but got {json_data}"
        assert 'not found' in json_data['error'].lower(), (
            f"Error message should mention image not found but got '{json_data['error']}'"
        )

    def test_pending_image_has_null_processed_at_timestamp(self, base_url, uploaded_image_id):
        """Test that pending images return null for processedAt timestamp"""
        response = requests.get(f"{base_url}/images/{uploaded_image_id}/status")
        json_data = response.json()
        
        if json_data['status'] == 'pending':
            assert json_data.get('processedAt') is None, (
                f"Pending images should have processedAt as null but got '{json_data.get('processedAt')}'"
            )


class TestTask4ImageDownload:
    """Test Task 4: GET /images/:id/download – Download Final Poster"""

    def test_completed_image_returns_binary_data_with_correct_content_type(self, base_url, completed_image_id):
        """Test that completed images return binary data with correct Content-Type"""
        response = requests.get(f"{base_url}/images/{completed_image_id}/download")
        
        assert response.status_code == 200, (
            f"Completed image download should return 200 OK but got {response.status_code}. "
            f"Response: {response.text if response.status_code != 200 else 'Binary data'}"
        )
        
        content_type = response.headers.get('content-type', '')
        assert content_type.startswith('image/'), (
            f"Content-Type should be image/* but got '{content_type}'"
        )
        
        assert len(response.content) > 0, (
            "Response should contain binary image data but content is empty"
        )

    def test_invalid_uuid_format_returns_400_bad_request(self, base_url):
        """Test that invalid UUID format returns 400 Bad Request"""
        invalid_uuid = "not-a-valid-uuid"
        response = requests.get(f"{base_url}/images/{invalid_uuid}/download")
        
        assert response.status_code == 400, (
            f"Invalid UUID should return 400 Bad Request but got {response.status_code}. "
            f"Response: {response.text}"
        )
        
        json_data = response.json()
        assert 'error' in json_data, f"Error response should contain 'error' field but got {json_data}"
        assert 'uuid' in json_data['error'].lower(), (
            f"Error message should mention UUID validation but got '{json_data['error']}'"
        )

    def test_nonexistent_image_returns_404_not_found(self, base_url):
        """Test that non-existent image returns 404 Not Found"""
        nonexistent_uuid = str(uuid.uuid4())
        response = requests.get(f"{base_url}/images/{nonexistent_uuid}/download")
        
        assert response.status_code == 404, (
            f"Non-existent image should return 404 Not Found but got {response.status_code}. "
            f"Response: {response.text}"
        )

    def test_unprocessed_image_returns_404_not_found(self, base_url, uploaded_image_id):
        """Test that unprocessed images return 404 Not Found"""
        response = requests.get(f"{base_url}/images/{uploaded_image_id}/download")
        
        # Should return 404 if image is not yet processed
        if response.status_code == 404:
            json_data = response.json()
            assert 'error' in json_data, f"Error response should contain 'error' field but got {json_data}"
            assert any(keyword in json_data['error'].lower() for keyword in ['not processed', 'not found']), (
                f"Error message should mention image not processed but got '{json_data['error']}'"
            )


class TestTask5ProcessTrigger:
    """Test Task 5: POST /images/:id/process – Trigger Processing"""

    def test_pending_image_can_be_triggered_for_processing(self, base_url, uploaded_image_id):
        """Test that valid pending images can be triggered for processing"""
        response = requests.post(f"{base_url}/images/{uploaded_image_id}/process")
        
        # Should return 200 OK or 409 if already processing
        assert response.status_code in [200, 409], (
            f"Process trigger should return 200 OK or 409 Conflict but got {response.status_code}. "
            f"Response: {response.text}"
        )
        
        if response.status_code == 200:
            json_data = response.json()
            assert 'id' in json_data, f"Response should contain 'id' field but got {json_data}"
            assert 'status' in json_data, f"Response should contain 'status' field but got {json_data}"
            assert json_data['id'] == uploaded_image_id, (
                f"Response ID should match requested ID but got '{json_data['id']}'"
            )
            assert json_data['status'] == 'processing', (
                f"Status should be 'processing' after trigger but got '{json_data['status']}'"
            )

    def test_invalid_uuid_format_returns_400_bad_request(self, base_url):
        """Test that invalid UUID format returns 400 Bad Request"""
        invalid_uuid = "not-a-valid-uuid"
        response = requests.post(f"{base_url}/images/{invalid_uuid}/process")
        
        assert response.status_code == 400, (
            f"Invalid UUID should return 400 Bad Request but got {response.status_code}. "
            f"Response: {response.text}"
        )
        
        json_data = response.json()
        assert 'error' in json_data, f"Error response should contain 'error' field but got {json_data}"
        assert 'uuid' in json_data['error'].lower(), (
            f"Error message should mention UUID validation but got '{json_data['error']}'"
        )

    def test_nonexistent_image_returns_404_not_found(self, base_url):
        """Test that non-existent image returns 404 Not Found"""
        nonexistent_uuid = str(uuid.uuid4())
        response = requests.post(f"{base_url}/images/{nonexistent_uuid}/process")
        
        assert response.status_code == 404, (
            f"Non-existent image should return 404 Not Found but got {response.status_code}. "
            f"Response: {response.text}"
        )
        
        json_data = response.json()
        assert 'error' in json_data, f"Error response should contain 'error' field but got {json_data}"
        assert 'not found' in json_data['error'].lower(), (
            f"Error message should mention image not found but got '{json_data['error']}'"
        )

    def test_already_processing_image_returns_409_conflict(self, base_url, processing_image_id):
        """Test that already processing images return 409 Conflict"""
        response = requests.post(f"{base_url}/images/{processing_image_id}/process")
        
        assert response.status_code == 409, (
            f"Already processing image should return 409 Conflict but got {response.status_code}. "
            f"Response: {response.text}"
        )
        
        json_data = response.json()
        assert 'error' in json_data, f"Error response should contain 'error' field but got {json_data}"
        assert 'already' in json_data['error'].lower() and 'processing' in json_data['error'].lower(), (
            f"Error message should mention already processing but got '{json_data['error']}'"
        )


class TestTask6BackgroundWorker:
    """Test Task 6: Background Worker Implementation - Observable API Behavior"""

    def test_processing_image_eventually_transitions_to_completed_status(self, base_url, processing_image_id):
        """Test that processing images eventually transition to completed status"""
        max_wait_time = 30  # seconds
        check_interval = 1  # second
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            response = requests.get(f"{base_url}/images/{processing_image_id}/status")
            if response.status_code == 200:
                json_data = response.json()
                status = json_data['status']
                
                if status == 'completed':
                    assert json_data.get('processedAt') is not None, (
                        "Completed images should have processedAt timestamp set"
                    )
                    return
                elif status == 'failed':
                    pytest.fail(f"Image processing failed. Status: {json_data}")
                
            time.sleep(check_interval)
        
        pytest.fail(f"Image did not complete processing within {max_wait_time} seconds")

    def test_processed_image_file_exists_and_accessible_via_download(self, base_url, completed_image_id):
        """Test that processed images are saved correctly and accessible via download"""
        response = requests.get(f"{base_url}/images/{completed_image_id}/download")
        
        assert response.status_code == 200, (
            f"Completed image should be downloadable but got {response.status_code}. "
            f"Response: {response.text if response.status_code != 200 else 'Binary data'}"
        )
        
        assert len(response.content) > 0, (
            "Downloaded image should not be empty"
        )
        
        # Verify it's a valid image file
        try:
            img = Image.open(io.BytesIO(response.content))
            img.verify()
        except Exception as e:
            pytest.fail(f"Downloaded file should be a valid image but got error: {e}")


class TestTask7AdminListView:
    """Test Task 7: GET /images – Admin List View"""

    def test_get_all_images_returns_paginated_list_with_default_limit(self, base_url):
        """Test that GET /images returns paginated list with default limit"""
        response = requests.get(f"{base_url}/images")
        
        assert response.status_code == 200, (
            f"Admin list view should return 200 OK but got {response.status_code}. "
            f"Response: {response.text}"
        )
        
        json_data = response.json()
        assert isinstance(json_data, list), (
            f"Response should be a list but got {type(json_data)}: {json_data}"
        )
        
        # Should respect default limit (10 items max)
        assert len(json_data) <= 10, (
            f"Default response should contain at most 10 items but got {len(json_data)}"
        )

    def test_status_filter_correctly_filters_results(self, base_url):
        """Test that status filter correctly filters results"""
        valid_statuses = ['pending', 'processing', 'completed', 'failed']
        
        for status in valid_statuses:
            response = requests.get(f"{base_url}/images?status={status}")
            
            assert response.status_code == 200, (
                f"Status filter '{status}' should return 200 OK but got {response.status_code}. "
                f"Response: {response.text}"
            )
            
            json_data = response.json()
            for item in json_data:
                assert item['status'] == status, (
                    f"All items should have status '{status}' but found item with status '{item['status']}'"
                )

    def test_pagination_parameters_work_correctly(self, base_url):
        """Test that pagination parameters (limit/offset) work correctly"""
        # Test limit parameter
        response = requests.get(f"{base_url}/images?limit=5")
        assert response.status_code == 200, (
            f"Limit parameter should work but got {response.status_code}. Response: {response.text}"
        )
        
        json_data = response.json()
        assert len(json_data) <= 5, (
            f"Response with limit=5 should contain at most 5 items but got {len(json_data)}"
        )
        
        # Test offset parameter
        response = requests.get(f"{base_url}/images?limit=5&offset=0")
        assert response.status_code == 200, (
            f"Offset parameter should work but got {response.status_code}. Response: {response.text}"
        )

    def test_invalid_status_filter_returns_400_bad_request(self, base_url):
        """Test that invalid status values return 400 Bad Request"""
        invalid_status = "invalid_status"
        response = requests.get(f"{base_url}/images?status={invalid_status}")
        
        assert response.status_code == 400, (
            f"Invalid status filter should return 400 Bad Request but got {response.status_code}. "
            f"Response: {response.text}"
        )
        
        json_data = response.json()
        assert 'error' in json_data, f"Error response should contain 'error' field but got {json_data}"
        assert 'invalid status' in json_data['error'].lower(), (
            f"Error message should mention invalid status but got '{json_data['error']}'"
        )

    def test_invalid_pagination_parameters_return_400_bad_request(self, base_url):
        """Test that invalid pagination parameters return 400 Bad Request"""
        # Test limit > 100
        response = requests.get(f"{base_url}/images?limit=150")
        assert response.status_code == 400, (
            f"Limit > 100 should return 400 Bad Request but got {response.status_code}"
        )
        
        # Test negative offset
        response = requests.get(f"{base_url}/images?offset=-1")
        assert response.status_code == 400, (
            f"Negative offset should return 400 Bad Request but got {response.status_code}"
        )
        
        # Test limit = 0
        response = requests.get(f"{base_url}/images?limit=0")
        assert response.status_code == 400, (
            f"Limit = 0 should return 400 Bad Request but got {response.status_code}"
        )

    def test_empty_results_return_200_with_empty_array(self, base_url):
        """Test that empty results return 200 OK with empty array"""
        # Use a very high offset to likely get empty results
        response = requests.get(f"{base_url}/images?offset=10000")
        
        assert response.status_code == 200, (
            f"Empty results should return 200 OK but got {response.status_code}. "
            f"Response: {response.text}"
        )
        
        json_data = response.json()
        assert isinstance(json_data, list), (
            f"Response should be a list even when empty but got {type(json_data)}"
        )

    def test_response_includes_all_required_fields(self, base_url):
        """Test that response includes all required fields for each image"""
        response = requests.get(f"{base_url}/images")
        json_data = response.json()
        
        if len(json_data) > 0:
            item = json_data[0]
            required_fields = ['id', 'filename', 'status', 'createdAt']
            
            for field in required_fields:
                assert field in item, (
                    f"Each image item should contain '{field}' field but got {item}"
                )
            
            # Validate UUID format
            try:
                uuid.UUID(item['id'])
            except ValueError:
                pytest.fail(f"Image ID should be valid UUID but got '{item['id']}'")


class TestTask8SignedUrl:
    """Test Task 8 (Optional): GET /images/:id/signed-url"""

    def test_completed_image_returns_valid_signed_url(self, base_url, completed_image_id):
        """Test that completed images return a valid signed URL"""
        response = requests.get(f"{base_url}/images/{completed_image_id}/signed-url")
        
        assert response.status_code == 200, (
            f"Completed image signed URL should return 200 OK but got {response.status_code}. "
            f"Response: {response.text}"
        )
        
        json_data = response.json()
        assert 'url' in json_data, f"Response should contain 'url' field but got {json_data}"
        
        signed_url = json_data['url']
        assert signed_url.startswith('http'), (
            f"Signed URL should be a valid URL but got '{signed_url}'"
        )
        
        # Should contain the image ID
        assert completed_image_id in signed_url, (
            f"Signed URL should contain image ID '{completed_image_id}' but got '{signed_url}'"
        )

    def test_invalid_uuid_format_returns_400_bad_request(self, base_url):
        """Test that invalid UUID format returns 400 Bad Request"""
        invalid_uuid = "not-a-valid-uuid"
        response = requests.get(f"{base_url}/images/{invalid_uuid}/signed-url")
        
        assert response.status_code == 400, (
            f"Invalid UUID should return 400 Bad Request but got {response.status_code}. "
            f"Response: {response.text}"
        )
        
        json_data = response.json()
        assert 'error' in json_data, f"Error response should contain 'error' field but got {json_data}"
        assert 'uuid' in json_data['error'].lower(), (
            f"Error message should mention UUID validation but got '{json_data['error']}'"
        )

    def test_nonexistent_image_returns_404_not_found(self, base_url):
        """Test that non-existent images return 404 Not Found"""
        nonexistent_uuid = str(uuid.uuid4())
        response = requests.get(f"{base_url}/images/{nonexistent_uuid}/signed-url")
        
        assert response.status_code == 404, (
            f"Non-existent image should return 404 Not Found but got {response.status_code}. "
            f"Response: {response.text}"
        )
        
        json_data = response.json()
        assert 'error' in json_data, f"Error response should contain 'error' field but got {json_data}"
        assert 'not found' in json_data['error'].lower(), (
            f"Error message should mention image not found but got '{json_data['error']}'"
        )

    def test_uncompleted_image_returns_403_forbidden(self, base_url, uploaded_image_id):
        """Test that non-completed images return 403 Forbidden"""
        response = requests.get(f"{base_url}/images/{uploaded_image_id}/signed-url")
        
        # Should return 403 if image is not completed
        if response.status_code == 403:
            json_data = response.json()
            assert 'error' in json_data, f"Error response should contain 'error' field but got {json_data}"
            assert any(keyword in json_data['error'].lower() for keyword in ['not completed', 'forbidden']), (
                f"Error message should mention image not completed but got '{json_data['error']}'"
            )

    def test_signed_url_includes_expiration_information(self, base_url, completed_image_id):
        """Test that signed URLs include expiration timestamp"""
        response = requests.get(f"{base_url}/images/{completed_image_id}/signed-url")
        
        if response.status_code == 200:
            json_data = response.json()
            signed_url = json_data['url']
            
            # Should contain expiration information (timestamp or expires parameter)
            assert any(keyword in signed_url.lower() for keyword in ['expires', 'exp', 'token']), (
                f"Signed URL should contain expiration information but got '{signed_url}'"
            ) 