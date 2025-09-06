FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Seoul

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src
COPY run.sh /app/run.sh

# Normalize CRLF and ensure exec bit
RUN sed -i 's/\r$//' /app/run.sh && chmod +x /app/run.sh

VOLUME ["/data"]

CMD ["/bin/sh","/app/run.sh"]
