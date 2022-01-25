FROM python:3.10.1-slim-bullseye

# Install and update dependencies
RUN apt-get -q update
RUN apt-get install -y gnupg curl

# Java Azul Zulu  Installation
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 0xB1998361219BD9C9
RUN curl -O https://cdn.azul.com/zulu/bin/zulu-repo_1.0.0-3_all.deb
RUN apt-get install -y ./zulu-repo_1.0.0-3_all.deb
RUN apt-get update
RUN apt-get install -y zulu11-jdk-headless

#NOTE: We should create a user account
RUN mkdir -p /usr/src/app

WORKDIR /usr/src/app

COPY ./requirements.txt /usr/src/app/

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

EXPOSE 8080

ENTRYPOINT ["python3"]

CMD ["-m", "swagger_server"]
