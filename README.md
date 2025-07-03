# Wanted Poster Generator API Test Suite

This is a comprehensive test suite for the Wanted Poster Generator API, testing all functional requirements from the specification.

## Test Structure

The test suite is organized into separate test classes for each task:

- **TestTask1HealthCheck** - Health endpoint validation (`GET /health`)
- **TestTask2ImageUpload** - Image upload functionality (`POST /images`)
- **TestTask3StatusCheck** - Status checking endpoint (`GET /images/:id/status`)
- **TestTask4ImageDownload** - Image download endpoint (`GET /images/:id/download`)
- **TestTask5ProcessTrigger** - Processing trigger endpoint (`POST /images/:id/process`)
- **TestTask6BackgroundWorker** - Background worker behavior (observable through API)
- **TestTask7AdminListView** - Admin list view with pagination (`GET /images`)
- **TestTask8SignedUrl** - Signed URL generation (`GET /images/:id/signed-url`)

## Running Tests

### Prerequisites

1. **API Server**: Ensure your API server is running and accessible
2. **Environment Variable**: Set `API_BASE_URL` if your API is not running on `http://localhost:8000`

### Local Execution

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run specific test class
pytest test_wanted_poster_api.py::TestTask1HealthCheck

# Run with verbose output
pytest -v

# Generate HTML report
pytest --html=report.html
```

### Docker Execution

```bash
# Build the test container
docker build -t wanted-poster-tests .

# Run tests (assuming API is on host machine)
docker run --network="host" wanted-poster-tests

# Run tests with custom API URL
docker run -e API_BASE_URL=http://your-api-host:8000 wanted-poster-tests

# Extract test results
docker run -v $(pwd)/test-reports:/app/test-reports wanted-poster-tests
```

## Configuration

### Environment Variables

- `API_BASE_URL`: Base URL for the API under test (default: `http://localhost:8000`)

### Test Fixtures

The test suite includes several fixtures that automatically create test data:

- `uploaded_image_id`: Creates a test image and returns its ID
- `processing_image_id`: Triggers processing on an uploaded image
- `completed_image_id`: Returns an image ID that should be completed
- `failed_image_id`: Returns an image ID that should be in failed status

## Test Coverage

### Happy Path Tests
- Successful image uploads (JPEG/PNG)
- Status checking with valid UUIDs
- Downloading completed images
- Triggering processing
- Admin list view with pagination
- Signed URL generation

### Sad Path Tests
- Invalid file types and sizes
- Invalid UUID formats
- Non-existent resources
- Invalid query parameters
- Already processing images
- Unauthorized access attempts

### Edge Cases
- Empty responses
- Large file uploads (>5MB)
- Pagination boundary conditions
- Status transitions
- Error message validation

## Test Assertions

All test assertions are designed to be highly descriptive, providing clear information about what went wrong without needing to examine the test code.

Example assertion:
```python
assert response.status_code == 201, (
    f"Valid image upload should return 201 Created but got {response.status_code}. "
    f"Response: {response.text}"
)
```

## Output

The test suite generates:
- Console output with detailed test results
- JUnit XML report (`test-reports/results.xml`) for CI/CD integration
- Optional HTML reports for detailed analysis

## Architecture

- **pytest framework**: Modern, feature-rich testing framework
- **requests library**: HTTP client for API testing
- **Pillow (PIL)**: Image manipulation for test data creation
- **Descriptive assertions**: Clear error messages for easy debugging
- **Fixture-based setup**: Automatic test data creation and cleanup 