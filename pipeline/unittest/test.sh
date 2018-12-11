#!/bin/bash
set -e
# esnure that no old containe is there
docker rm -f tng-sdk-project || true
# start container
docker run --rm -d -p 5098:5098 --name tng-sdk-project registry.sonata-nfv.eu:5000/tng-sdk-project
# trigger unittests
docker exec -i tng-sdk-project pytest --tavern-beta-new-traceback
# kill the container
docker rm -f tng-sdk-project