#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

from enum import Enum


class ResultLevel(Enum):
    ERROR = 1
    WARNING = 2
    INFORMATION = 3


class Result:
    def __init__(self):
        self.messages: list[(ResultLevel, str)] = []
        self.warning_count: int = 0
        self.error_count: int = 0

    def __iadd__(self, other):
        self.error_count = self.error_count + other.error_count
        self.warning_count = self.warning_count + other.warning_count
        self.messages = self.messages + other.messages
        return self

    def with_error(self, error):
        self.error_count += 1
        self.messages.append((ResultLevel.ERROR, error))

    def with_warning(self, warning):
        self.warning_count += 1
        self.messages.append((ResultLevel.WARNING, warning))

    def with_information(self, information):
        self.messages.append((ResultLevel.INFORMATION, information))


def validate(project, request, response, validators):
    # TODO: move this code to the UI module
    # json_response = json.loads(response.text)
    # logger.info(json.dumps(json_response, sort_keys=True, indent=3))
    # logger.info(f"Request completed in {elapsed_time:0.2f} seconds.")

    result = Result()
    for _validate in validators:
        result += _validate(project, request, response)

    return result
    # TODO: move this logic to the UI module to display validation results
    # for severity, message in result.messages:
    #     if severity.value <= verbosity:
    #         if severity.value == 1:
    #             logger.error(message)
    #         elif severity.value == 2:
    #             logger.warning(message)
    #         else:
    #             logger.info(message)
    # validation_file_path = os.path.join(project.path, "logs", "validation.log")
    # write_validation_log(validation_file_path, result)
    #
    # if len(result.messages) > 0:
    #     logger.info(f"All validation logs written to '{validation_file_path}'")
    # if result.error_count > 0 and verbosity < 1:
    #     logger.error(f"Found {result.error_count} errors when validating response")
    # if result.warning_count > 0 and verbosity < 2:
    #     logger.warning(f"Found {result.warning_count} warnings when validating response")
    # if result.error_count + result.warning_count == 0:
    #     logger.info("Validation passed with no errors", extra={"style": "class:success"})
