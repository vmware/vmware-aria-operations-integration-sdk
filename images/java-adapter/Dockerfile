FROM base-adapter:python-1.0.0

# Switch to root to install Java
USER root

# Install dependencies, add Azul repository, and install JDK 17
RUN apt-get -q update && \
    apt-get -yq install gnupg wget ca-certificates && \
    update-ca-certificates && \
    mkdir -p /etc/apt/keyrings && \
    (wget -qO- https://repos.azul.com/azul-repo.key || wget --no-check-certificate -qO- https://repos.azul.com/azul-repo.key) | gpg --dearmor -o /etc/apt/keyrings/azul.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/azul.gpg] http://repos.azul.com/zulu/deb stable main" > /etc/apt/sources.list.d/zulu.list && \
    apt-get -q update && \
    apt-get install -y zulu17-ca-jdk-headless && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Switch back to the least privileged user
USER aria-ops-adapter-user
