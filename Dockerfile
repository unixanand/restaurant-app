FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Oracle Instant Client
RUN apt-get update && apt-get install -y \
    libaio1 \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/* \
    && wget --no-check-certificate https://download.oracle.com/otn_software/linux/instantclient/2110000/instantclient-basiclite-linux.x64-21.1.0.0.0.zip \
    && unzip instantclient-basiclite-linux.x64-21.1.0.0.0.zip -d /opt/oracle \
    && rm instantclient-basiclite-linux.x64-21.1.0.0.0.zip \
    && echo "/opt/oracle/instantclient_21_1" > /etc/ld.so.conf.d/oracle-instantclient.conf \
    && ldconfig \
    && apt-get clean

COPY . .

EXPOSE 8501

ENV ORACLE_HOME=/opt/oracle/instantclient_21_1
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_21_1:$LD_LIBRARY_PATH

CMD ["streamlit", "run", "restaurantapp.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]