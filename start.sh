#!/bin/sh
cd /app/backend
exec python3 -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
