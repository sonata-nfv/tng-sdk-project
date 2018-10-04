#!/bin/bash
set -e
docker run --rm -d -p 5098:5098 --name tng-sdk-project registry.sonata-nfv.eu:5000/tng-sdk-project
docker exec -i tng-sdk-project pytest --tavern-beta-new-traceback
docker stop tng-sdk-project