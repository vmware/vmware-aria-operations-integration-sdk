#!/usr/bin/env python3

import connexion
import logging

from swagger_server import encoder


def main():
    try:
        logging.basicConfig(filename='/var/log/server.log',
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)
        logger = logging.getLogger('waitress')
        logger.setLevel(logging.DEBUG)
    except Exception as e:
        logging.basicConfig(level=logging.CRITICAL+1)

    app = connexion.App(__name__, specification_dir='./swagger/')
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('swagger.yaml', arguments={'title': 'Adapter API'}, pythonic_params=True, validate_responses=True)

    # development server
    # app.run(port=8080)

    # production server
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)


if __name__ == '__main__':
    main()
