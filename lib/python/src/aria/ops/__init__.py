#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import logging
from logging import NullHandler

# Add a null handler to avoid 'No Handler Found' warnings if the library user hasn't
# configured their own.
logging.getLogger(__name__).addHandler(NullHandler())
