# Runner Image

Sandboxed container for executing user-submitted code.

## Security Features

- Runs as non-root user
- Resource limits (CPU, memory, time) to be configured
- Network isolation to be implemented
- Read-only filesystem (except /tmp) to be configured

## Usage

This image is intended to be spawned by the worker service to execute code submissions in isolation.

## TODO

- Add resource limiting via Docker run flags
- Implement code execution entrypoint
- Add language-specific runtimes
