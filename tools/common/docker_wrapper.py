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
            print("Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?")
        elif "PermissionError" in e.args[0]:
            print(f"Cannoct run docker commands. Make sure the user {os.getlogin()} has permisions to run docker")
        else:
            print(f"Unexpected error when stablishing connection with Docker daemon: {e}")

        raise InitError

def push_image(client, image_tag):
    """
    Pushes the given image tag and returns the images digest.

    If there is an error during while pushing the image, then it will gerenate a
    PushError, that the user can handle

    NOTE: An alternate method of parsing the digest from an image would be to
    parse the attributes of an image and then check if the image has repoDigests
    attribute, then we could parse the repo digest (different from digest) to get the digest.


    :param client: the docker client that comunicates to the docker daemon
    :param image_tag: An image tag that identifies the image to be pushed
    :return: A string version of the SHA256 digest
    """
    response = client.images.push(image_tag, stream=True, decode=True)

    image_digest = ""

    for line in response:
        if 'aux' in line:
            try:
                image_digest = line['aux']['Digest']
            except KeyError:
                print(f"Image Digest was not found in response from server")
                raise PushError

        elif 'errorDetail' in line:
            print(f"{line['errorDetail']['message']}")
            raise PushError

    return image_digest

def build_image(client, path, tag):
    try:
        return  client.images.build(path=path, tag=tag, nocache=True, rm=True)
    except docker.errors.BuildError as error:
        print(f"An error ocurred while trying to build docker image at {path}")
        print(error)
        raise BuildError


class InitError(Exception):
    """Raised when there is an error starting the docker client"""
    pass

class PushError(Exception):
    """Raised when the registry server sends back an error"""
    pass

class BuildError(Exception):
    """Raised when and error occurs while building the Docker image"""
    pass
