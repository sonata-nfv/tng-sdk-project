#!/bin/bash
set -e
echo "checking style ..."
docker run -i --rm registry.sonata-nfv.eu:5000/tng-sdk-project flake8 src --exclude .eggs --max-line-length 120
docker run -i --rm registry.sonata-nfv.eu:5000/tng-sdk-project flake8 tests --max-line-length 120
echo "done."
