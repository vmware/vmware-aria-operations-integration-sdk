import docker

from common.config import get_config_values, get_config_value
from common.filesystem import get_absolute_project_directory


def main():
    client = docker.from_env()
    registry_url = login(client)

    # TODO: Prompt user to increment
    version = get_config_value("version")
    repo = get_config_value("docker_repo", "tvs")

    # TODO: Prompt user to select which images to build? e.g., python, java, powershell
    build_path = get_absolute_project_directory("python-flask-adapter")
    python, python_logs = client.images.build(path=build_path, nocache=True, rm=True,
                                              tag=f"vrops-adapter-open-sdk-server:python-{version}")

    tags = [
        f"vrops-adapter-open-sdk-server:python-{version}",
        f"vrops-adapter-open-sdk-server:python-{version.split('.')[0]}",
        f"vrops-adapter-open-sdk-server:python-latest"
    ]
    for tag in tags:
        print(f"pushing tag {tag}")
        python.tag(tag)
        registry_tag = f"{registry_url}/{repo}/{tag}"
        python.tag(registry_tag)
        client.images.push(registry_tag)

    print("Successfully pushed tags:")
    for tag in tags:
        print(f"    {tag}")
    print(f"To registry {registry_url}")


def login(docker_client):
    docker_login_config = get_config_values("username", "password", "registry_url",
                                            defaults={"registry_url": "harbor-repo.vmware.com"})

    docker_client.login(
        username=docker_login_config["username"],
        password=docker_login_config["password"],
        registry=docker_login_config["registry_url"]
    )

    return docker_login_config["registry_url"]


if __name__ == '__main__':
    main()
