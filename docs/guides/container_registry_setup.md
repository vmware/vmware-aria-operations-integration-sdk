# Setting up a Container Registry

Management Packs created by the Integration SDK use Adapters that are distributed by container registries. 
A _container registry_ has at least one _repository_ that stores and provides access to container images.
For more information about how the Adapter Container Image distribution works, see [Management Pack Distribution](../references/architecture.md#management-pack-distribution).

The container registry is a key component of this distribution model, and as such it is required when building a Management Pack (i.e., using [`mp-build`](../references/mp-build.md))

Any container registry should work if it is set up so that:
* You have write access to a repository for pushing an image
* The repository is public, so that the image can be pulled anonymously (e.g., without first doing a `docker login`)
* The registry is accessible by your VMware Aria Operations Cloud Proxies

The following are known to work.

## Using the 'Harbor' Container Registry

1. Install Harbor, if necessary. Ensure that the network you install it into is accessible from both your development environment and the VMware Aria Operations Cloud Proxies.

      **Install Harbor using a Tanzu Tile**
      :  Harbor can be installed as a Tanzu Tile. Instructions can be found here: [https://docs.vmware.com/en/VMware-Harbor-Registry/services/vmware-harbor-registry/GUID-installing.html](https://docs.vmware.com/en/VMware-Harbor-Registry/services/vmware-harbor-registry/GUID-installing.html).

      **Install Harbor on vSphere**
      :  Harbor can be installed as an OVA on vSphere. The following guide walks through the process (The context of the guide is for deploying a TGK registry, but the process is the same):
         [https://docs.vmware.com/en/VMware-Tanzu-Kubernetes-Grid/2.2/tkg-deploy-mc-22/mgmt-reqs-harbor.html](https://docs.vmware.com/en/VMware-Tanzu-Kubernetes-Grid/2.2/tkg-deploy-mc-22/mgmt-reqs-harbor.html)

      **Installing Harbor Directly**
      :  The Harbor project has installation guides for installing Harbor on [Docker](https://goharbor.io/docs/2.9.0/install-config/) and [Kubernetes via Helm](https://goharbor.io/docs/2.9.0/install-config/harbor-ha-helm/).

2. Create a [Public Repository](https://goharbor.io/docs/2.0.0/working-with-projects/create-projects/)

    ???+ note

        VMware Aria Operations pulls images anonymously, which requires the repository to be public.
        For more information, see the FAQ: [I can't use a public repository. Are there any options?](troubleshooting_and_faq/container_registries.md#i-cant-use-a-public-repository-are-there-any-options)

3. Run `mp-build` and set the registry and repository tag when prompted (may look like `harbor.my-organization.com/my-project/adaptername`)

    ??? note

        If `mp-build` doesn't prompt for a tag for the container repository, open the `config.json` file in the project's root directory, then replace the key-value of `container_repository` with the tag.

4. Once step `3` is successful, subsequent builds will no longer require any of the above steps.

## Using a Cloud-based Container Registry

### Using an AWS container registry

AWS container registries use `aws` CLI to authenticate, so users should authenticate to their AWS container registry and create a repository before
running `mp-build`.

1. [Log in to your registry using aws CLI](https://docs.aws.amazon.com/AmazonECR/latest/userguide/getting-started-cli.html#cli-authenticate-registry)
2. [Create a repository](https://docs.aws.amazon.com/AmazonECR/latest/userguide/getting-started-cli.html#cli-create-repository:~:text=your%20default%20registry-,Step%203%3A%20Create%20a%20repository,-Step%204%3A%20Push)

    ???+ note

        VMware Aria Operations pulls images anonymously, which requires the repository to be public.
        For more information, see the FAQ: [I can't use a public repository. Are there any options?](troubleshooting_and_faq/container_registries.md#i-cant-use-a-public-repository-are-there-any-options)

3. Run `mp-build` and set the registry and repository when prompted (usually looks like `aws_account_id.dkr.ecr.region.amazonaws.com/repository-for-test-mp`)

    ??? note

        If `mp-build` doesn't prompt for a tag for the container repository, open the `config.json` file in the project's root directory, then replace the key-value of `container_repository` with the tag.
 
4. Once step `3` is successful, subsequent builds will no longer require any of the above steps.

### Using Docker Hub

!!! warning

    VMware Aria Operations only supports anonymous pulling of images, which may cause issues when using Docker Hub since there is a [Download rate limit](https://docs.docker.com/docker-hub/download-rate-limit/#:~:text=Docker%20Hub%20limits%20the%20number,pulls%20per%206%20hour%20period). 

Docker CLI recommends using a token when using docker hub instead of your login password, so users should authenticate their Docker Hub account before running `mp-build`.

1. Go to [Docker Hub](https://hub.docker.com/repository/create?) and create a new repository
 
    ???+ note

        VMware Aria Operations pulls images anonymously, which requires the repository to be public.
        For more information, see the FAQ: [I can't use a public repository. Are there any options?](troubleshooting_and_faq/container_registries.md#i-cant-use-a-public-repository-are-there-any-options)

2. Login to docker hub using the CLI docker login

    ```{ .shell .copy}
    docker login
    ```

3. Run `mp-build`. When prompted for the container registry and repository, use the following format:

    ``` {.shell .copy}
    docker.io/USER_NAME/CONTAINER_REPOSITORY
    ```
    The `USER_NAME` should be the same username used to login into docker hub in step 3, and the `CONTAINER_REPOSITORY` should be the registry created in step one.
    After entering the tag, you will be prompted to enter your credentials to log into Docker Hub. Enter the same credentials used in step 2.

    ??? note

        If `mp-build` doesn't prompt for a tag for the container repository, open the `config.json` file in the project's root directory, then replace the key-value of `container_repository` with the tag.

4. Once step `3` is successful, subsequent builds will no longer require any of the above steps.