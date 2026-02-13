FROM python:3.12-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash runner
WORKDIR /home/runner

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY run.py harness.py ./

USER runner

ENTRYPOINT ["python", "run.py"]
