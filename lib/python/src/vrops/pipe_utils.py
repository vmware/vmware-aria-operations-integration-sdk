import json
import logging
from typing import Union

logger = logging.getLogger(__file__)


def read_from_pipe(input_pipe: str) -> Union[dict, list]:
    logger.debug(f"Input Pipe: {input_pipe}")
    try:
        with open(input_pipe, "r") as input_file:
            logger.debug(f"Opened {input_file.name}")
            return json.load(input_file)
    except Exception as e:
        logger.error("Error when reading from Input Pipe.")
        logger.debug(e)
    logger.debug("Finished reading Input Pipe")


def write_to_pipe(output_pipe: str, result: Union[dict, list]):
    logger.debug(repr(result))
    logger.debug(f"Output Pipe: {output_pipe}")
    try:
        with open(output_pipe, "w") as output_file:
            logger.debug(f"Opened {output_pipe}")
            json.dump(result, output_file)
            logger.debug(f"Closing {output_pipe}")
    except Exception as e:
        logger.error("Error when writing to Output Pipe.")
        logger.debug(e)
    logger.debug("Finished writing results to Output Pipe")
