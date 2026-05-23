FROM python:3.9-slim
RUN apt-get update && apt-get install -y ffmpeg gcc python3-dev
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY . .
CMD ["python", "main.py"]
