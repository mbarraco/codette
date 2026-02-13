FROM python:3.12-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash grader
USER grader
WORKDIR /home/grader

# Placeholder entrypoint
CMD ["python", "-c", "print('Grader placeholder - not implemented yet')"]
