FROM python:3.11.6-alpine3.18

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    libatomic \
    linux-headers \
    git

# Install grpcio and other Python dependencies
RUN pip install grpcio


ENV SERVICE_NAME="ted"

WORKDIR /home
COPY . .

WORKDIR /home/
RUN pip install pip --upgrade
RUN pip install --no-cache-dir --upgrade -r requirements.txt

EXPOSE 8000

##--reload
CMD ["uvicorn", "src.ted_app.main:ted", "--host", "0.0.0.0","--workers", "4"]