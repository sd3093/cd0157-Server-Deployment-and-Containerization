# Use the official `python:3.11` image from the Amazon ECR Public Gallery
# (a mirror of the Docker Hub image, so there is no Docker Hub pull rate limit).
FROM public.ecr.aws/docker/library/python:3.11

# Set up an app directory for your code
COPY . /app
WORKDIR /app

# Install `pip` and needed Python packages from `requirements.txt`
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Define an entrypoint which will run the main app using the Gunicorn WSGI server.
ENTRYPOINT ["gunicorn", "-b", ":8080", "main:APP"]
