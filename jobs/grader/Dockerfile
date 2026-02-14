FROM python:3.12-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash grader
WORKDIR /home/grader

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY grade.py .

USER grader

ENTRYPOINT ["python", "grade.py"]
