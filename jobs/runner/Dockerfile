FROM python:3.12-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash runner
WORKDIR /home/runner

# Install dependencies
COPY runner/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code as a package
COPY errors.py ./
COPY runner/__init__.py runner/run.py runner/harness.py runner/schemas.py ./runner/

USER runner

ENTRYPOINT ["python", "-m", "runner.run"]
