FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

# Strip Windows line endings from the entrypoint script
RUN sed -i 's/\r//' entrypoint.sh && chmod +x entrypoint.sh

CMD ["bash", "./entrypoint.sh"]
