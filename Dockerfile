# set base image (host OS)
FROM python:3.9.2

# copy the content of the local directory to the working directory
COPY . .

# install dependencies
RUN pip install -r requirements.txt

# command to run on container start
CMD [ "python", "./main.py" ]