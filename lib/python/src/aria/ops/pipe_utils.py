#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
import logging
from typing import Optional
from typing import Union

logger = logging.getLogger(__name__)


def read_from_pipe(input_pipe: str) -> Optional[dict | list]:
    logger.debug(f"Input Pipe: {input_pipe}")
    try:
        with open(input_pipe, "r") as input_file:
            logger.debug(f"Opened {input_file.name}")
            return json.load(input_file)  # type: ignore[no-any-return]
    except Exception as e:
        logger.error("Error when reading from Input Pipe.")
        logger.debug(e)
        return None


def write_to_pipe(output_pipe: str, result: Optional[dict | list]) -> None:
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
    logger.debug("Finished writing results to Output Pipe.")
