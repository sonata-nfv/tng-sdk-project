#!/bin/bash
mkdir -p reports
docker run -i --rm registry.sonata-nfv.eu:5000/tng-sdk-project pycodestyle --exclude .eggs . > reports/checkstyle-pep8.txt
cat reports/checkstyle-pep8.txt

# always exit with 0 (ugly code style is not an error :))
#exit 0
