FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Run as non-root user
RUN useradd -m labuser
USER labuser

EXPOSE 5000

CMD ["python", "app.py"]
