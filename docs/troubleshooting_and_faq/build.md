# mp-build


### mp-build returns 'Unable to build pak file'

In most cases, this error indicates issues with building the container image. The most probable causes are:

<ol>
<li>Unknown Instruction:</li>

```
mp-build
Building adapter [Finished]
Unable to build pak file
ERROR: Unable to build Docker file at /Users/user/code/aria_ops/management-packs/test:
 {'message': 'dockerfile parse error line 7: unknown instruction: COP'}

```

<li>A command inside the Dockerfile failed:</li>

```
mp-build
Building adapter [Finished]
Unable to build pak file
ERROR: Unable to build Docker file at /Users/user/code/management-packs/test:
 The command '/bin/sh -c pip3 install -r adapter_requirements.txt --upgrade' returned a non-zero code: 1
```

TODO: this is no longer the case, now the docker error will be displayed.
We should also make it the case for both of them

The solution for case 1 is to fix the typo/command by editing the Dockerfile.
For case 2, however, the solution might not be evident at first sight.
Since the error comes from building the image itself,
we can run `docker build .` in the project's root directory and look at the stack trace for clues.
</ol>

???+ info

    For issues regarding mp-build and docker, see [Docker's](docker.md) page.

