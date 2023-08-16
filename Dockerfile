FROM python:latest

ENV SERVICE_NAME="ted"

WORKDIR /home
COPY . .

WORKDIR /home/
RUN pip install pip --upgrade 
RUN pip install --no-cache-dir --upgrade -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "src.ted_app.main:ted", "--host", "0.0.0.0","--reload"]