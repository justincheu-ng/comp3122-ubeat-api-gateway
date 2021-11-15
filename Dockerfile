FROM python:3.8

WORKDIR /app/
COPY api_gateway.py requirements.txt /app/
RUN pip install -r requirements.txt --no-cache-dir

CMD python api_gateway.py