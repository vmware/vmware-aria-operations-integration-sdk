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

The base OS is Debian for security and
licensing reasons. For more information go [here](https://confluence.eng.vmware.com/display/OS/Container+Base+OS).

#### Building Images
All commands are run from the root folder of the project and assume that the image built is the current latest version.
The next section will cover tags and their conventions.

1. Build base image
```
docker build --no-cache python-flask-adapter  --tag vrops-adapter-open-sdk-server:python
```
2. Build powershell image
```
docker build --no-cache python-flask-adapter  --tag vrops-adapter-open-sdk-server:powershell
```
3. Build java image
```
docker build --no-cache python-flask-adapter  --tag vrops-adapter-open-sdk-server:java
```

#### [Docker Tag](https://docs.docker.com/engine/reference/commandline/tag/)
Tags differentiate characteristics of the built image. The following sections describe the tags used in the base images.

##### Server Version
The main component in the project is the HTTP Server defined by the vROps collector API. Therefore, the image version is based on the API version and follows [semantic versioning](https://semver.org/).

##### Stable Tags
A stable tag is used by an image to convey a specific characteristic.
In the words of a more articulate person, "Stable tags mean a developer, or a build system, can continue to pull a
specific tag, which continues to get updates. Stable doesn’t mean the contents are frozen. Rather, stable implies
the image should be stable for the intent of that version. To stay “stable”, it might be serviced to apply security
patches or framework updates.([Steve Lasker](https://docs.microsoft.com/en-us/azure/container-registry/container-registry-image-tag-version#:~:text=Stable%20tags%20mean,or%20framework%20updates.))". Our stable tag convention is as follows:

- [LANGUAGE]: points to the latest stable tag, no matter what the current major version is
- [LANGUAGE]-[MAJOR_VERSION]: points to the latest stable image of the specific major version
- [LANGUAGE]-[SERVER_VERSION]: the main language supported by the image other than python, followed by server version.

The image below is a visual representation  of stable tags with a similar semantic, but is not an actual representation of our semantic.
![docker tags](https://stevelaskerblog.files.wordpress.com/2018/03/stabletagging.gif)

##### Language
The main language supported by the generated container. We currently support `python`,`java`, and `powershell`;
However, users are encourage to use the base image and install their own desired language. Our base image is
vrops-adapter-open-sdk-server:python, because the base image requires python to run the `swagger_server`, and all
images depend on the swagger server as a middle man between vROps and the user's adapter.

Each components will determine the tags used by an image in our project.
The template below shows where each components should be for any image generated
in our project:

 - vrops-adapter-open-sdk-server:[LANGUAGE]-[VERSION]

This image should then be tagged by any additional applicable tags using the
following template:

 - vrops-adapter-open-sdk-server:[LANGUAGE]-[STABLE-TAG]



## [Harbor](https://confluence.eng.vmware.com/display/HARBOR/Harbor)

### What is it?
Harbor is an open source container image registry that secures images
with role-based access control, scans images for vulnerabilities, and signs
images as trusted. A CNCF Incubating project, Harbor delivers compliance, performance,
and interoperability to help you consistently and securely manage images across cloud
native compute platforms like Kubernetes and Docker.

### Why use it?
First an foremost, Harbor is VMware solution which gives us a lot of control over the way
we use it without having to worry about Dockerhub liabilities and so on. Second, Harbor has a
self serve platform that allows us to request projects for internal or external distribution
on the fly without much overhead. Finally, unlike our Artifactory project, we have full control
of our project.

### Pulling Images

1. Make sure you have access to harbor by login into [https://harbor-repo.vmware.com/harbor/projects](https://harbor-repo.vmware.com/harbor/projects),
then go to [https://harbor-repo.vmware.com/harbor/projects/1067689/members](https://harbor-repo.vmware.com/harbor/projects/1067689/members), and ensure you are a member of the project.

2. login into harbor through the docker cli
```
docker login harbor-repo.vmware.com
```

3. Pull any image inside the `vrops-adapter-open-sdk-server`  repo to ensure everything is working. The command
bellow will pull the latest version of the python image.
```
docker pull harbor-repo.vmware.com/tvs/vrops-adapter-open-sdk-server:python
```
Another method is to go directly to the image you want do download and click icon right next to the artifact hash and under the pull command.

### Pushing Images
For the purpose of this example we are going use push the base image generated by the Dockerfile located in the python-flask-adapter. However the
process will be the same for any other image, with the exception of the tag name. See the Docker Tag section to understand the tag conventions.

1. login into harbor through the docker cli (if you are already logged, skip this step)
```
docker login harbor-repo.vmware.com
```

2. build and tag image
```
docker build --no-cache python-flask-adapter --tag harbor-repo.vmware.com/tvs/vrops-adapter-open-sdk-server:python-0.1.0
```

3. push tagged image
```
docker push harbor-repo.vmware.com/tvs/vrops-adapter-open-sdk-server:python-0.1.0

```
