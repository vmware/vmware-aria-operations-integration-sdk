FROM base-adapter:python-1.0.0
# manual java install to prevent overwriting previous dependencies
# switch to root in order to do all installs
USER root

# install the necessary dependencies and update CA certificates
RUN  apt-get -q update && \
     apt-get -yq install gnupg wget ca-certificates && \
     update-ca-certificates && \
     apt-get clean && \
     rm -rf /var/lib/apt/lists/*

# add Azul's public key and repository
# Using wget with --no-check-certificate as a fallback since the base image might not have proper certs
RUN  mkdir -p /etc/apt/keyrings && \
     (wget -qO- https://repos.azul.com/azul-repo.key || wget --no-check-certificate -qO- https://repos.azul.com/azul-repo.key) | gpg --dearmor -o /etc/apt/keyrings/azul.gpg && \
     echo "deb [signed-by=/etc/apt/keyrings/azul.gpg] http://repos.azul.com/zulu/deb stable main" > /etc/apt/sources.list.d/zulu.list

# update the package sources and install Azul Zulu JDK 17
RUN  apt-get -q update && \
     apt-get install -y zulu17-ca-jdk-headless && \
     apt-get clean && \
     rm -rf /var/lib/apt/lists/*

#switch back to the LPU
USER aria-ops-adapter-user
