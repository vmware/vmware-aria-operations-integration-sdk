from common.config import get_config_values


def login(docker_client):
    # This is where we should get the credentials from the config file, and they aren't present
    # we should ask the user for them, and update the config file.
    docker_login_config = get_config_values("username", "password", "registry_url",
                                            defaults={"registry_url": "harbor-repo.vmware.com"})

    docker_client.login(
        username=docker_login_config["username"],
        password=docker_login_config["password"],
        registry=docker_login_config["registry_url"]
    )

    return docker_login_config["registry_url"]
