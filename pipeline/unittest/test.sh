#!/bin/bash
set -e
# start container
docker run --rm -d -p 5098:5098 --name tng-sdk-project registry.sonata-nfv.eu:5000/tng-sdk-project
# trigger unittests
docker exec -i tng-sdk-project pytest --tavern-beta-new-traceback
# trigger integration tests
docker exec -i tng-sdk-project pipeline/unittest/test_sdk_integration.sh
# kill the container
docker rm -f tng-sdk-project