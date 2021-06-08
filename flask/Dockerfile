FROM python:3.9
RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install flask pymongo
RUN mkdir /app
RUN mkdir -p /app/data
COPY main.py /app/main.py
ADD data /app/data
EXPOSE 5000
WORKDIR /app
CMD ["python","-u","/app/main.py"]


