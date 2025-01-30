# Container Registries


### Why do I need a container registry?

Containerized adapters use container registries to store, distribute, and install adapters. During the development of an
adapter, mp-build requires a container registry to upload the resulting container. After uploading the container to the
given registry, `mp-build` saves the host, and the container digest in the `<ADAPTERNAME>.conf` file bundled inside the pak
file. During installation, VCF Operations uses the information inside the `<ADAPTERNAME>.conf` file to pull the
container from the registry and run the container.

---
### What requirements are there for a container registry?

Any container registry should work if it is set up so that:

* You have write access to a repository for pushing an image
* The repository is public, so that the image can be pulled anonymously (e.g., without first doing a `docker login`)
* The registry is accessible by your VCF Operations Cloud Proxies

---
### How can I setup a container registry for my project?

See [Setting up a Container Registry](../guides/container_registry_setup.md)

---
### How can I change the container registry for my project?

Open the `config.json` file located in the project's root directory, then replace the key-value for `container_repository` with the tag of the
repository you want to use. The next time `mp-build` is run, the new tag will be used and validated.

---
### How are registry credentials managed?

The Docker daemon manages docker credentials. To learn more about how the docker daemon manages credentials,
visit the docker [credential store page](https://docs.docker.com/engine/reference/commandline/login/#credentials-store)

---
### I can't use a public repository. Are there any options?

The container registry needs to be accessible from the VCF Operations Cloud Proxy(ies) that it will run on. Thus, in most cases
where a Management Pack is being deployed within an intranet, the container registry does not need to be accessible to the Internet.
However, because VCF Operations pulls images anonymously, the repository cannot require access controls for pulling (downloading)
an image. This is commonly known as a public repository. 

However, for development purposes, there may be situations where it is convenient to temporarily use a private registry. In such cases,
there is a workaround. Cloud proxies lookup images locally before attempting to pull, so the following process can be used:

1. Build the Management Pack as usual, specifying the private registry.
2. SSH into the cloud proxy where the adapter is going to run.
3. Login to docker (usually using `docker login`), and pull the adapter container image used by the management pack. 
   This _must_ have the same image digest SHA that the management pack specifies. 

    ???+ note

        The Digest SHA can be found by unzipping the `.pak` file, then unzipping the `adapter.zip`. The image digest can be found in the 
        file `<ADAPTERNAME>.conf` as the value of the `DIGEST` key.

4. Install Management Pack in VCF operations
