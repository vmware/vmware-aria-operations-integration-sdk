#!/usr/bin/env python3
#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import os

import connexion
import server_logging
from cheroot import wsgi
from cheroot.ssl.builtin import BuiltinSSLAdapter
from swagger_server import encoder


def main() -> None:
    server_logging.setup_logging("server.log")
    logger = server_logging.getLogger("main")

    app = connexion.App(__name__, specification_dir="swagger/")
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api(
        "swagger.yaml",
        arguments={"title": "Adapter API"},
        pythonic_params=True,
        validate_responses=False,
    )

    ssl_cert = "/etc/ssl/certs/dockerized.crt"
    ssl_key = "/etc/ssl/certs/dockerized.key"
    port = 8080
    if os.path.exists(ssl_cert) and os.path.exists(ssl_key):
        port = 443

    logger.info(f"Port: {port}")

    # production server
    server = wsgi.Server(("0.0.0.0", port), app)
    if port == 443:
        server.ssl_adapter = BuiltinSSLAdapter(ssl_cert, ssl_key, None)
    server.start()


if __name__ == "__main__":
    main()
