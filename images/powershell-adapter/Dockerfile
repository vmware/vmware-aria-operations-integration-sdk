FROM base-adapter:python-1.0.0

# Switch to root to install PowerShell
USER root

# Install dependencies, add Microsoft repository, and install PowerShell
RUN apt-get -q update && \
    apt-get -yq install wget ca-certificates && \
    wget -q https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    rm packages-microsoft-prod.deb && \
    apt-get -q update && \
    apt-get install -y powershell && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Switch back to the least privileged user
USER aria-ops-adapter-user
