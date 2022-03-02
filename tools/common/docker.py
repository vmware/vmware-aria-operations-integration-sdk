from common.config import get_config_values


def login(docker_client):
    docker_login_config = get_config_values("username", "password", "registry_url",
                                            defaults={"registry_url": "harbor-repo.vmware.com"})

    docker_client.login(
        username=docker_login_config["username"],
        password=docker_login_config["password"],
        registry=docker_login_config["registry_url"]
    )

    return docker_login_config["registry_url"]
