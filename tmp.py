from importlib import resources

import parso

from vmware_aria_operations_integration_sdk import adapter_template


def line_contains_keyword(line: str, keywords: list[str]) -> bool:
    return any(keyword in line for keyword in keywords)


def filter_code(source_code: str, keywords: list[str]) -> str:
    # Parse the source code
    module = parso.parse(source_code)

    # Initialize an empty list to accumulate the filtered lines
    filtered_code = []

    # Iterate over all functions in the source code
    for function in module.iter_funcdefs():
        # If the function's name is 'collect', process it
        if function.name.value in [
            "get_adapter_definition",
            "test",
            "collect",
            "get_endpoints",
        ]:
            # Add the function definition line
            filtered_code.append(function.get_code().split("\n")[2])

            # Iterate over all children nodes in the function's body
            for child in function.children:
                # Check each individual line of the child node's code
                for line in child.get_code().split("\n"):
                    # Add lines containing any of the keywords
                    if line_contains_keyword(line, keywords):
                        filtered_code.append(line)

    # Join the filtered lines with newline characters and return the result
    return "\n".join(filtered_code)


source_code = resources.files(adapter_template).joinpath("adapter.py").read_text()
keywords = ["CollectResult()", "with", "try", "except", "return"]

filtered_module = filter_code(source_code, keywords)
print(filtered_module)
