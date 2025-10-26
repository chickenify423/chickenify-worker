FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y ffmpeg python3 python3-pip git

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

COPY . /app
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
