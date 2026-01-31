#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
PYTHONPATH=src python -m ollama_tui "$@"
