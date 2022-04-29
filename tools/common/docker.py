import subprocess

from common.config import get_config_value


def login():
    docker_registry = get_config_value("registry_url", default="harbor-repo.vmware.com")

    print(f"login into {docker_registry}")
    response = subprocess.run(["docker", "login", f"{docker_registry}"])

    # Since we are using a subprocess, we cannot be very specific about the type of failure we get
    if response.returncode != 0:
        raise LoginFailure

    return docker_registry


class LoginFailure(Exception):
    """Raised when the subprocess fails"""
    pass
