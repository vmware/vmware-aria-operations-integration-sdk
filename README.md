# Development

TODO

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

### Pulling and Pushing Images

1. Make sure you have access to harbor by login into [https://harbor-repo.vmware.com/harbor/projects](https://harbor-repo.vmware.com/harbor/projects),
then go to [https://harbor-repo.vmware.com/harbor/projects/1067689/members](https://harbor-repo.vmware.com/harbor/projects/1067689/members), and ensure you are a member of the project.

2. login into harbor through the docker cli
```
docker login harbor-repo.vmware.com
```

3. Pull any image inside the `vrops-adapter-open-sdk-server`  repo to ensure everything is working
