#!/bin/bash
set -e
echo "checking style ..."
docker run -i --rm registry.sonata-nfv.eu:5000/tng-sdk-project pycodestyle --exclude .eggs
echo "done."
