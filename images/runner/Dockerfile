FROM python:3.12-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash runner
USER runner
WORKDIR /home/runner

# Placeholder entrypoint
CMD ["python", "-c", "print('Runner placeholder - not implemented yet')"]
