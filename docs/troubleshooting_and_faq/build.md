# mp-build

### mp-build returns 'Unable to build pak file'

In most cases, this error indicates issues with building the container image. The most probable cause is:

```
mp-build
Building adapter [Finished]
Unable to build pak file
ERROR: Unable to build Docker file at /Users/user/code/aria_ops/management-packs/test:
 {'message': 'dockerfile parse error line 7: unknown instruction: COP'}

```

In cases where build is unable to complete the building process due to a docker error, 
the best approach is to look at the stack trace from docker by directly running `docker build .` 
command.

???+ info

    For issues regarding mp-build and docker, see [Docker's](docker.md) page.

