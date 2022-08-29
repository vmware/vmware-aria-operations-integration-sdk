# Python Project

## Structure
```
.
├── Dockerfile
├── adapter_requirements.txt
├── app
│   └── adapter.py
├── commands.cfg
├── conf
│   └── describe.xml
├── content
│   ├── dashboards
│   ├── files
│   └── reports
├── manifest.txt
└── resources
    └── resources.properties
```
### Dockerfile (file)
Contains all necessary instructions to build a container with an HTTP server, the user's executable Adapter
code, and any additional dependencies specified by the user.

### adapter_requirements.txt (file)
TODO  talk about pip3 install -r
Contains all python dependencies needed by the adapter. This file will be used during the construction of the container
to ensure all dependencies are included in the container.

### app (directory)
Contains all the source adapter source code. This directory is copied into the container defined by the Dockerfile.
### adapter.py (file)
 - This file is used by the HTTP server to server request made by the vRealize Operations Manager.
 - the HTTP server passes each request in the form of a parameter, and reads the responses through stdout.
 - To re-define the file the HTTP server uses to perform HTTP requests for the server, the user should modify the commands.cfg file.
 - The adapter uses the python vROps library (TODO create the vROps Library)
 - API calls table
| Request/Parameter  | Description   |
| :----------------: | :------------ |
| test               | The adapter should test connection to the server| TODO define what test connection looks like
| collect            | The adapter should run a collection and return a list of all collected objects|

TODO link the swagger API, so the use can see all requests

### commands.cfg (file)
This files contains a list of the commands the HTTP server can run, along with the path to the executable related to the command. By default, all commands are run by executing the adapter.py file along with a parameter that defines a command. For example; when the HTTP server receives a request to run a test connection, it reads the commands.cfg key for `test` and runs the process defined by the key value.

### conf Folder (directory)
   - describe.xml: An XML configuration file that defines the object model for an adapter, along with semantic definitions for use in data analysis and management.

### content Folder(directory)
This folder contains all the components included in a management pack such as: alerts, groups, dashboards, policies, recommendations, reports, resources, supermetrics, symptoms, and traversal specs.
#### dashboards (directory)
TODO: Provide sample dashboard

#### files (directory)
TODO: what should be inside this directory ?

#### reports (directory)
TODO: what are reports ?

### manifest.txt (file)
The manifest file contains top-level information that you need to install and maintain a management pack.
TODO: create table for manifest file properties
| Manifest Property  | Value         |
| :----------------: | :------------ |
| Content Cell       | Content Cell  |
| Content Cell       | Content Cell  |

### resources (directory)
A file that contains English labels for various objects. vROps supports localization, so users can add additional file(s) to support other languages.
To support another language, create a file with resources_[LANGUAGE_CODE].properties, then vROps will use the appropriate labels when set to that language.
#### resources.properties (file)
TODO: Add example file