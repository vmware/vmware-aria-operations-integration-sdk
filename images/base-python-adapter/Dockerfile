FROM python:3.11.1-slim-bullseye

# Ensure that the /var/log directory is writable by the server/adapter
RUN chmod 777 /var/log

# Create LPU and create/set work directory
RUN useradd --create-home --shell /bin/bash aria-ops-adapter-user
USER aria-ops-adapter-user
WORKDIR /home/aria-ops-adapter-user/src/app

# Copy project into container and install requirements
COPY . .
RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 443
EXPOSE 8080

ENTRYPOINT ["python3"]
CMD ["-m", "swagger_server"]
