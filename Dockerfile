FROM python:3.7.3-alpine
RUN apk add --no-cache bash
RUN mkdir -p /watchdir
ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt
CMD ["python", "monitor_failed.py"]