#!/bin/bash
set -e
# Helper script that runs parts of the CI/CD pipeline locally
# Can be used to check code before pushing/pull request

# check style early
flake8 src --exclude .eggs --max-line-length 120
flake8 tests --max-line-length 120

# always dump swagger api spec
tng-project --dump-swagger

# execute pipeline: build, test, check, integration
pipeline/build/build.sh
pipeline/unittest/test.sh
pipeline/checkstyle/check.sh
docker run --rm --name tng-sdk-project-int registry.sonata-nfv.eu:5000/tng-sdk-project pipeline/unittest/test_sdk_integration.sh
