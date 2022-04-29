import subprocess

from common.config import get_config_value


def login(docker_client):
    # This is where we should get the credentials from the config file, and they aren't present
    # we should ask the user for them, and update the config file.
    docker_registry = get_config_value("registry_url", default="harbor-repo.vmware.com")

    print(f"login into {docker_registry}")
    subprocess.run(["docker", "login", f"{docker_registry}"])

    return docker_registry
