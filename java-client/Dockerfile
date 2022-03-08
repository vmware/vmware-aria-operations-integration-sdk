FROM vrops-adapter-open-sdk-server:python-0.3.0

# manual java install to prevent overwriting previous dependencies
# switch to root in oder to do all installs
USER root

# install the necessary dependencies
RUN  apt-get -q update
RUN  apt-get -yq install gnupg curl

# add Azul's public key
RUN  apt-key adv \
  --keyserver hkp://keyserver.ubuntu.com:80 \
  --recv-keys 0xB1998361219BD9C9

# download and install the package that adds
# the Azul APT repository to the list of sources
RUN curl -O https://cdn.azul.com/zulu/bin/zulu-repo_1.0.0-3_all.deb

# install the package
RUN  apt-get install ./zulu-repo_1.0.0-3_all.deb

# update the package sources
RUN  apt-get update

# install Azul Zulu JDK 17
RUN apt-get install -y zulu17-ca-jdk-headless #NOTE:maybe we could get away with just having the JRE since the user should provide executables

#switch back to the LPU
USER vrops-adapter-user
