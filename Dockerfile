# set base image (host OS)
FROM balenalib/raspberry-pi-debian-python:latest

RUN install_packages gcc \
    libc-dev \
    && rm -rf /var/cache/apk/*

# copy the content of the local directory to the working directory
COPY . .

# install dependencies
RUN pip install -r requirements.txt

# command to run on container start
CMD [ "python", "./main.py" ]