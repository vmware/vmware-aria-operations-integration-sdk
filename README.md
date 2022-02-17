# Development
* * *
### Docker
There are three different images in this project:
- vrops-adapter-open-sdk-server:python (base image)
	- Uses python:3.10.2-slim-bullseye as its base image
	- Contains the swagger_server used by vROps to communicate with the adapter
- vrops-adapter-open-sdk-server:java
	- Uses vrops-adapter-open-sdk-server:python as its base image
	- Contains Zulu 17 headless JDK
- vrops-adapter-open-sdk-server:powershell
	- Uses vrops-adapter-open-sdk-server:python as its base image
	- Contains debian version of powershell

The base OS is Debian for security and licensing reasons. For more information go [here](https://confluence.eng.vmware.com/display/OS/Container+Base+OS).

#### Building Images
All commands are run from the root folder of the project and assume that the version of the http server is `0.3.0`.
The next section will cover tags and their conventions.

1. Build base image
```
docker build --no-cache python-flask-adapter  --tag vrops-adapter-open-sdk-server:python-0.3.0
```
2. Build powershell image
```
docker build --no-cache python-flask-adapter  --tag vrops-adapter-open-sdk-server:powershell-0.3.0
```
3. Build java image
```
docker build --no-cache python-flask-adapter  --tag vrops-adapter-open-sdk-server:java-0.3.0
```

#### Tagging Convention
Tags differentiate characteristics of the built image. Every image must have a _unique tag_, plus optional additional tags known as _stable tags_:

>   Stable tags mean a developer, or a build system, can continue to pull a specific tag, which
>   continues to get updates. Stable doesn’t mean the contents are frozen. Rather, stable implies the image
>   should be stable for the intent of that version. To stay “stable”, it might be serviced to apply
>   patches or framework updates.([Steve Lasker](https://docs.microsoft.com/en-us/azure/container-registry/container-registry-image-tag-version#:~:text=Stable%20tags%20mean,or%20framework%20updates.)).

##### Unique Tag
Each image should have a unique tag with the following format:

- [LANGUAGE]-[SERVER_VERSION]: the main language supported by the image, followed by server version.

###### Language
The language component of a tag specifies the main language supported by the generated container.
Language is one of `python`,`java`, or `powershell`. If an unsupported language is desired, the base
image `vrops-adapter-open-sdk-server:python` can be used as a starting point to install an additional
language or runtime environment. The base image contains the HTTP server, which is required to serve
calls from vROps and the user's adapter. It is also possible to start from a different base image,
but in this case an HTTP server that conforms to the collector API must be manually added.

###### Server Version
The main component in the project is the HTTP Server defined by the vROps collector API. Therefore, the image version is based on the API version and follows [semantic versioning](https://semver.org/).


##### Stable Tags
The stable tag convention for this project is as follows:

- [LANGUAGE]-latest: points to the latest stable tag, no matter what the current major version is
- [LANGUAGE]-[MAJOR_VERSION]: points to the latest stable image of the specific major version

The graphic below shows how stable and unique tags are assigned over time in a project with a similar tag convention:
![docker tags](https://stevelaskerblog.files.wordpress.com/2018/03/stabletagging.gif)


The template below shows where each component should be for any image generated
in the project:

 - vrops-adapter-open-sdk-server:[LANGUAGE]-[VERSION]

This image should then be tagged by any additional applicable tags using the
following template:

 - vrops-adapter-open-sdk-server:[LANGUAGE]-[STABLE-TAG]

#### Tagging Images
Images should always be tagged with the unique tag at build time. This example uses an image with
unique tag `python-0.3.0`.

1. Determine which stable tags apply to the image.
	- Since this image is stable and is the latest stable version for the major release 0,  `python-0` should be applied to it.
	- Since the major release 0 is also the latest major release, 'python-latest' should be applied to it.
2. Apply the stable tags to image:
	```
	docker tag vrops-adapter-open-sdk-server:python-0.3.0 vrops-adapter-open-sdk-server:python-0
	docker tag vrops-adapter-open-sdk-server:python-0.3.0 vrops-adapter-open-sdk-server:python-latest
	```

## [Harbor](https://confluence.eng.vmware.com/display/HARBOR/Harbor)

### What is it?
Harbor is an open source container image registry that secures images
with role-based access control, scans images for vulnerabilities, and signs
images as trusted. A Cloud Native Computing Foundation Incubating project, Harbor delivers compliance, performance,
and interoperability to consistently and securely manage images across cloud
native compute platforms like Kubernetes and Docker.

### Why use it?
Harbor is a VMware platform that allows full control of projects for internal or external distribution
without the liabilities of an externally hosted solution like Dockerhub.

### Pulling Images

1. Make sure you have access to Harbor by logging in to [https://harbor-repo.vmware.com/harbor/projects](https://harbor-repo.vmware.com/harbor/projects),
then go to [https://harbor-repo.vmware.com/harbor/projects/1067689/members](https://harbor-repo.vmware.com/harbor/projects/1067689/members), and ensure you are a member of the project.
	- If you can't log in to Harbor, contact the Harbor team through their slack app [@Harbor](https://cloud-native.slack.com/messages/harbor)
	- If you are not a member of this team, contact any of members listed as admins

2. Log in to harbor through the Docker CLI:
```
docker login harbor-repo.vmware.com
```

3. Pull any image inside the `vrops-adapter-open-sdk-server`  repo to ensure login worked. The command
bellow will pull the latest version of the Python image.
```
docker pull harbor-repo.vmware.com/tvs/vrops-adapter-open-sdk-server:python
```
Images can also be downloaded through the Harbor web UI by clicking the icon next to the artifact hash (under the pull command).
### Pushing Images
Before pushing and image to Harbor make sure the image has a unique tag and any applicable stable tags

1. Log in to Harbor through the Docker CLI (if you are already logged in, skip this step):
```
docker login harbor-repo.vmware.com
```

2. For every image tag, add an additional tag with the prefix `harbor-repo.vmware.com/tvs/`:
```
docker tag vrops-adapter-open-sdk-server:python-0.3.0 harbor-repo.vmware.com/tvs/vrops-adapter-open-sdk-server:python-0.3.0
docker tag vrops-adapter-open-sdk-server:python-0 harbor-repo.vmware.com/tvs/vrops-adapter-open-sdk-server:python-0
docker tag vrops-adapter-open-sdk-server:python-latest harbor-repo.vmware.com/tvs/vrops-adapter-open-sdk-server:python-latest
```

3. Push all tagged images:
```
docker push harbor-repo.vmware.com/tvs/vrops-adapter-open-sdk-server:python-0.3.0
docker push harbor-repo.vmware.com/tvs/vrops-adapter-open-sdk-server:python-0
docker push harbor-repo.vmware.com/tvs/vrops-adapter-open-sdk-server:python-latest
```
