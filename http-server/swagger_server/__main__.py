#!/usr/bin/env python3
import logging
import os

import connexion
# production server
from waitress import serve

from swagger_server import encoder


def main():
    try:
        logging.basicConfig(filename="/var/log/server.log",
                            filemode="a",
                            format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
                            datefmt="%H:%M:%S",
                            level=logging.DEBUG)
        logger = logging.getLogger("waitress")
        logger.setLevel(logging.DEBUG)
    except Exception as e:
        logging.basicConfig(level=logging.CRITICAL + 1)

    app = connexion.App(__name__, specification_dir="./swagger/")
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api("swagger.yaml", arguments={"title": "Adapter API"}, pythonic_params=True, validate_responses=False)

    # development server
    # app.run(port=8080)

    scheme = "http"
    if len(os.listdir("/Certs")) > 0:
        scheme = "https"
    serve(app, host="0.0.0.0", port=8080, url_scheme=scheme)


if __name__ == "__main__":
    main()
