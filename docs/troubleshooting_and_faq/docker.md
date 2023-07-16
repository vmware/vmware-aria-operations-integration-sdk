# Docker


### When starting Docker, I get 'Permission denied while trying to connect to the Docker daemon'

If you're having trouble getting Docker to run on your system, you can refer to the Docker documentation for instructions
on how to start Docker on [macOS](https://docs.docker.com/docker-for-mac/install/), [Linux](https://docs.docker.com/desktop/install/debian/#launch-docker-desktop), and [Windows 10 and 11](https://docs.docker.com/desktop/install/windows-install/#start-docker-desktop).

### When starting Docker on Windows, I get 'Cannot connect to Docker daemon'

If you're having trouble with permissions on a Windows system, you can refer to the Docker documentation for instructions
on how to [Understand permission requirements for Windows](https://docs.docker.com/desktop/windows/permission-requirements/).

### When using mp-test and mp-build, I get a "Cannot connect to the Docker daemon" error

There are multiple causes for this error; the most common causes and solutions are:

1. The Docker daemon is not running. Possible solutions are:
    - Open the Desktop application
    - See Docker's documentation for [starting the daemon](https://docs.docker.com/config/daemon/start/) using OS utilities
    - See Docker's documentation for [troubleshooting the Docker daemon](https://docs.docker.com/config/daemon/troubleshoot/)

2. The Docker daemon is running, but the socket is not open or accessible. Possible solutions are:
    - Open Docker Desktop application :fontawesome-solid-arrow-right: navigate to :material-cog: (Settings) on the top right corner :fontawesome-solid-arrow-right: :material-cogs: Advanced :fontawesome-solid-arrow-right: make sure "Allow the default Docker socket to be used" is enabled.
    - Ensure permissions to access the Docker daemon socket are enabled:
        - For [MacOs](https://docs.docker.com/desktop/mac/permission-requirements/)
        - For [Windows](https://docs.docker.com/desktop/windows/permission-requirements/)
        - FOR [Linux](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user)

