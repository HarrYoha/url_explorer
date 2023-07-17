# Use the official Python base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN python --version

COPY ./src /app/src

WORKDIR /app/src


CMD ["python", "url_explorer_app.py"]
