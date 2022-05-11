import subprocess
import os
import docker


from common.config import get_config_value



def login():
    docker_registry = get_config_value("registry_url", default="harbor-repo.vmware.com")

    print(f"login into {docker_registry}")
    response = subprocess.run(["docker", "login", f"{docker_registry}"])

    # Since we are using a subprocess, we cannot be very specific about the type of failure we get
    if response.returncode != 0:
        raise LoginFailure

    return docker_registry

def init():
    """ Tries to sttablish a connection with the docker daemon via unix socket.

    If the connection fails, the error message is parsed to find a coomon error message that could inidicate that the
    daemon isn't running.
    If the message does not match the common error message, then the error is appended to another
    error message.

    :return:  A Docker Client that communicates with the Docker daemon
    """
    try:
        client = docker.from_env()

        return client
    except docker.errors.DockerException as e:
        if "ConnectionRefusedError" in e.args[0]:
            raise  DaemonError("Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?")
        elif "PermissionError" in e.args[0]:
            raise DockerGroupError(f"Cannoct run docker commands. Make sure the user {os.getlogin()} has permisions to run docker")

        else:
            raise InitFailure(f"Unexpected error when stablishing connection with Docker daemon: {e}")


class LoginFailure(Exception):
    """Raised when the subprocess fails"""
    pass

class InitFailure(Exception):
    """Raise for any unzatgorized errors during init"""
    pass

class DaemonError(Exception):
    """Raised when connection is refused when trying to connect to Docker daemon"""
    pass


print(f"client: {init()}")
