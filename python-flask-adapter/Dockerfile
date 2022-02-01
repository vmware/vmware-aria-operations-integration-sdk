FROM python:3.10.1-slim-bullseye

# Create LPU and create/set work directory
RUN useradd --create-home --shell /bin/bash vrops-adapter-user
USER vrops-adapter-user
WORKDIR /home/vrops-adapter-user/src/app

# Copy project into container and install requirements
COPY . .
RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 8080

ENTRYPOINT ["python3"]

CMD ["-m", "swagger_server"]
