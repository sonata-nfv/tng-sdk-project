#!/bin/bash
set -e
docker run -i --rm registry.sonata-nfv.eu:5000/tng-sdk-project:v4.0 pytest -v
