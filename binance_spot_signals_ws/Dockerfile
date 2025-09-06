# Add-on Dockerfile patch: normalize run.sh line endings and ensure +x
# Place this content in your existing Dockerfile replacing the RUN lines for run.sh
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Seoul

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src
COPY run.sh /app/run.sh

# Normalize potential CRLF and ensure executable bit
RUN sed -i 's/\r$//' /app/run.sh && chmod +x /app/run.sh

VOLUME ["/data"]

CMD ["/app/run.sh"]
