FROM python:3.13-slim

WORKDIR /app

# Copy the package and server directories
COPY pkg/ ./pkg/
COPY cmd/ ./cmd/

# Expose standard Redis port
EXPOSE 6379

# Set PYTHONPATH so Python can locate our pkg module
ENV PYTHONPATH=/app

# Run the database server
CMD ["python", "cmd/server/main.py"]
