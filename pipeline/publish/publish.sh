#!/bin/bash
set -e
docker push registry.sonata-nfv.eu:5000/tng-sdk-project

# publish to dev, which is then pushed to Docker Hub
echo 'Tagging and pushing :dev'
docker tag registry.sonata-nfv.eu:5000/tng-sdk-project:latest sonatanfv/tng-sdk-project:dev
docker push sonatanfv/tng-sdk-project:dev
