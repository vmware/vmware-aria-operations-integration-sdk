FROM base-adapter:python-0.9.0

# manual powershell install to prevent overwritting previous dependecies
# switch to root in oder to do all installs
USER root

# install the necessary dependencies
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y wget

# download and install the package that adds
# the Powershell  APT repository to the list of sources
RUN wget https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb
RUN dpkg -i packages-microsoft-prod.deb

# update the package sources
RUN apt-get update

# install Powershell
RUN apt-get install -y  powershell

#switch back to the LPU
USER aria-ops-adapter-user
