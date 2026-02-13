# Grader Image

Container for comparing submission output against expected results.

## Purpose

- Receives runner output and expected output
- Performs comparison (exact match, floating point tolerance, etc.)
- Returns grade result (pass/fail, partial credit)

## Usage

This image is intended to be spawned by the worker service after the runner completes.

## TODO

- Implement grading logic
- Support multiple comparison modes
- Add partial credit scoring
