# Use Python 3.10 image from Docker Hub
FROM python:3.10

# Set the working directory inside the container to /code
WORKDIR /code

# Copy the requirements.txt file to /code directory inside the container
COPY ./requirements.txt /code/requirements.txt

# Upgrade pip and install required Python packages from requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the application folder into the /code/app directory inside the container
COPY ./app /code/app

# Set the command to run main.py when the container starts
CMD ["python", "/code/app/main.py"]
