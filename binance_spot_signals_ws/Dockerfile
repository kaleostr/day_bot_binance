ARG BUILD_FROM
FROM $BUILD_FROM

# Keep Python slim & install deps
RUN apk add --no-cache python3 py3-pip tzdata

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# App files
WORKDIR /opt/app
COPY requirements.txt /opt/requirements.txt
RUN python3 -m pip install --no-cache-dir -r /opt/requirements.txt

COPY src /opt/app/src
COPY run.sh /run.sh
RUN chmod a+x /run.sh && sed -i 's/\r$//' /run.sh

# S6 overlay entrypoint (per HA docs)
CMD ["/run.sh"]
