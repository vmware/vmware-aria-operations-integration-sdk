FROM projects.registry.vmware.com/vmware_aria_operations_integration_sdk/base-adapter:python-0.11.0
COPY commands.cfg .
COPY adapter_requirements.txt .

RUN pip3 install -r adapter_requirements.txt
COPY app app
