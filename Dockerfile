# Based on the example at https://cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-service

# Getting base image
FROM python:3.10-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Adding the necessary files, like app.py, to the image
ADD . /

# Installing the necessary packages
RUN pip install --no-cache-dir flask==2.1.0
RUN pip install --no-cache-dir pandas==1.4.2
RUN pip install --no-cache-dir scipy==1.8.0
RUN pip install --no-cache-dir matplotlib==3.5.2
RUN pip install --no-cache-dir statsmodels==0.13.2
RUN pip install --no-cache-dir scikit-learn==1.0.2
RUN pip install --no-cache-dir gunicorn==20.1.0
RUN pip install --no-cache-dir gunicorn==20.1.0
RUN pip install --no-cache-dir pymongo==4.1.1

# Running the website
CMD exec gunicorn --bind 0.0.0.0:8000 --workers 1 --threads 8 --timeout 0 app:app
