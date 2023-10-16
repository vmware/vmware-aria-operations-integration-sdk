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

???+ info

    For issues regarding mp-build and docker, see [Docker's](docker.md) page.

