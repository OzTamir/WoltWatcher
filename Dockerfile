FROM python:3.9
COPY src/ /app
COPY my_config.json /app/config.json
COPY requirements.txt /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD python ./wolt_watcher.py