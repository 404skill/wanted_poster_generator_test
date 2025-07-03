# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

ENTRYPOINT ["bash", "-lc", "pytest --cache-clear --junitxml=test-reports/results.xml"] 