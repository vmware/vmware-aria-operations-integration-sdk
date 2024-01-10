# SNMP Template MP

## Requirements
- [Integration SDK](../../docs/get_started.md#requirements)
- vCenter Adapter Instance on VMware Aria Operations
- Container registry accessible to the cloud proxy where the vCenter MP Extension adapter will run.
 
## About the SNMP Template MP

The SNMP Template is designed to facilitate starting a new Management Pack using SNMP.

The Management Pack sets up a connection using SNMP v2 or v3 credentials, and runs 
several commands to retrieve some basic data. 

It is not intended to be useful on its own, rather it is a starting point for creating a 
management pack that uses SNMP.

## Usage
To modify this template , follow these steps:
1. Create a directory for the project, and copy the files inside the `snmp-template-mp`
     directory into it.
2. Create a virtual environment and install dependencies, for example by running 
   a. `python -m venv venv-snmp` - create virtual environment
   b. `source venv-snmp/bin/activate.sh` - activate virtual environment
   c. `pip install -r requirements.txt` - install tools and dev requirements
   d. `pip install -r adapter_requirements.txt` - install runtime requirements
3. Update the Solution Key/Name and Adapter Key/Name.
   The solution key is found in the `manifest.txt` file, and has the key `"name"`.
   The solution name is found in the `resources/resources.properties` file, and has the
   key `DISPLAY_NAME` (You may also want to modify the other values in the 
   `resources/resources.properties` file).
   The Adapter Key and Name are found in the `app/constants.py` file, and can be changed
   by modifying the `ADAPTER_KIND` and `ADAPTER_NAME` constants.
4. Modify the adapter as necessary to collect from the desired SNMP OIDs. The template
   code gets device info from the supplied host, and then creates objects for each
   interface on the device. These should be present on most devices that support SNMP. 
   The code can be left in place, modified, or deleted as necessary.

## Building
### Build pak file
- Run `mp-build` at the root of the sample project directory. `mp-build` uses the given container registry to 
  upload a container image that contains the adapter. The cloud proxy pulls the container image from the registry and
  runs the adapter inside the container. Consult the [Troubleshooting](../../docs/troubleshooting_and_faq/index.md) section for 
  additional information about setting up container registries.

