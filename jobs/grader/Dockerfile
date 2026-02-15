FROM python:3.12-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash grader
WORKDIR /home/grader

# Install dependencies
COPY grader/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code as a package
COPY errors.py ./
COPY grader/__init__.py grader/run.py grader/schemas.py ./grader/

USER grader

ENTRYPOINT ["python", "-m", "grader.run"]
