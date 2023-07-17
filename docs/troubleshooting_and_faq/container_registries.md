# Container Registries


### Why do I need a container registry?

Containerized adapters use container registries to store, distribute, and install adapters. During the development of an
adapter, mp-build requires a container registry to upload the resulting container. After uploading the container to the
given registry, `mp-build` saves the host, and the container digest in the `manifest.txt` file bundled inside the pak
file. During installation, VMware Aria Operations uses the information inside the `manifest.txt` file to pull the
container from the registry and run the container.

!!! info

    For help setting up a container registry see:

    - [How can I set up a private container registry for my project](#how-can-i-set-up-a-private-container-registry-for-my-project)
    - [How can I set up an AWS container registry for my project](#how-can-i-set-up-an-aws-container-registry-for-my-project)
    - [How can I set up a Docker Hub container registry for my project](#how-can-i-set-up-a-docker-hub-container-registry-for-my-project)

### How are registry credentials managed?

The Docker daemon manages docker credentials. To learn more about how the docker daemon manages credentials,
visit the docker [credential store page](https://docs.docker.com/engine/reference/commandline/login/#credentials-store)

### How can I set up an AWS container registry for my project?

!!! todo
    Add a note about registries being public

AWS container registries use `aws` CLI to authenticate, so users should authenticate to their AWS container registry and create a repository before
running `mp-build`.

1. [Log in to your registry using aws CLI](https://docs.aws.amazon.com/AmazonECR/latest/userguide/getting-started-cli.html#cli-authenticate-registry)
2. [Create a repository](https://docs.aws.amazon.com/AmazonECR/latest/userguide/getting-started-cli.html#cli-create-repository:~:text=your%20default%20registry-,Step%203%3A%20Create%20a%20repository,-Step%204%3A%20Push)
3. Run `mp-build` and use the registry tag when prompted about it (usually looks like `aws_account_id.dkr.ecr.region.amazonaws.com/hello-repository`)

### How can I set up a Docker Hub container registry for my project?

!!! warning

    VMware Aria Operations only supports anonymous pulling of images, which may cause issues when using Docker Hub since there is a [Download rate limit](https://docs.docker.com/docker-hub/download-rate-limit/#:~:text=Docker%20Hub%20limits%20the%20number,pulls%20per%206%20hour%20period). To use a private registry see [How can I set up a private container registry for my project?](#how-can-i-set-up-a-private-container-registry-for-my-project)

Docker CLI recommends using a token when using docker hub instead of your login password, so users should authenticate their Docker Hub account before running `mp-build`.

1. Go to [Docker Hub](https://hub.docker.com/repository/create?) and create a new repository
2. Login to docker hub using the CLI docker login

    ```{ .shell .copy}
    docker login
    ```

3. Run `mp-build`.When prompted about the tag for the container registry, use the following format:

    ``` {.shell .copy}
    docker.io/USER_NAME/CONTAINER_REPOSITORY
    ```
The `USER_NAME` should be the same username used to login into docker hub in step 3, and the `CONTAINER_REPOSITORY` should be the registry created in step one.
After entering the tag, you will be prompted to enter your credentials to log into Docker Hub. Enter the same credentials used in step 2.

???+ note

    If `mp-build` doesn't prompt for a tag for the container repository, open the `config.json` file in the project's root directory, then replace the key-value of `container_repository` with the tag.


### How can I set up a private container registry for my project?

VMware Aria Operations only supports anonymous pulling of images, however, cloud proxies lookup images locally before attempting to pull.

1. ssh into the cloud proxy where the adapter is going to be set up
2. pull the same image used by the management pack (usually using the docker CLI inside the adapter)
3. Install Management Pack in VMware Aria operations

### How can I change the container registry for my project?

Open the `config.json` file located in the project's root directory, then replace the key-value for `container_repository` with the tag of the
repository you want to use. The next time `mp-build` is run, the new tag will be used and validated.

