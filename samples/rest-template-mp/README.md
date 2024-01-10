# REST Template MP

## Requirements
- [Integration SDK](../../docs/get_started.md#requirements)
- vCenter Adapter Instance on VMware Aria Operations
- Container registry accessible to the cloud proxy where the vCenter MP Extension adapter will run.
 
## About the REST Template MP

The REST Template is designed to facilitate starting a new Management Pack using REST
requests. Note that in many cases, REST APIs will have a python library that wraps the
REST API. This is often preferable to using raw rest requests (as this template does),
as the library can handle setting up authentication, creating and formatting the
requests, and handling errors and transforming the output.

This management pack is not intended to be useful on its own, rather it is a starting 
point for creating a management pack that uses REST requests.

## Usage
To modify this template , follow these steps:
1. Create a directory for the project, and copy the files inside the `rest-template-mp`
     directory into it.
2. Create a virtual environment and install dependencies, for example by running 
   a. `python -m venv venv-rest` - create virtual environment
   b. `source venv-rest/bin/activate.sh` - activate virtual environment
   c. `pip install -r requirements.txt` - install tools and dev requirements
   d. `pip install -r adapter_requirements.txt` - install runtime requirements
3. Update the Solution Key/Name and Adapter Key/Name.
   The solution key is found in the `manifest.txt` file, and has the key `"name"`.
   The solution name is found in the `resources/resources.properties` file, and has the
   key `DISPLAY_NAME` (You may also want to modify the other values in the 
   `resources/resources.properties` file).
   The Adapter Key and Name are found in the `app/constants.py` file, and can be changed
   by modifying the `ADAPTER_KIND` and `ADAPTER_NAME` constants.
4. Modify the adapter as necessary to create and process REST requests. The template
   code gets project info from a PyPi server (the supplied host), and then creates 
   objects for each supplied project on the server. This is a simple set of GET requests
   that do not require authentication, but samples and links are in the code to provide
   starting places

## Building
### Build pak file
- Run `mp-build` at the root of the sample project directory. `mp-build` uses the given container registry to 
  upload a container image that contains the adapter. The cloud proxy pulls the container image from the registry and
  runs the adapter inside the container. Consult the [Troubleshooting](../../docs/troubleshooting_and_faq/index.md) section for 
  additional information about setting up container registries.

