#!/bin/bash
set -e
docker push registry.sonata-nfv.eu:5000/tng-sdk-project

echo 'Tagging and pushing'
docker tag registry.sonata-nfv.eu:5000/tng-sdk-project:latest sonatanfv/tng-sdk-project:latest
docker push sonatanfv/tng-sdk-project:latest
