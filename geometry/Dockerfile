FROM python:3.11-slim

# System dependencies for Shapely (GEOS) and reportlab
RUN apt-get update && apt-get install -y \
    libgeos-dev \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies first (layer caching)
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    pydantic \
    shapely \
    numpy \
    ezdxf \
    reportlab \
    scipy \
    pydantic-settings

# Copy application code and ensure appuser can read everything
COPY app/ ./app/

EXPOSE 8000

RUN useradd -r -s /bin/false appuser && \
    chmod -R a+rX /app
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
