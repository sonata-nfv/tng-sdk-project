#!/bin/bash
set -e
set -x
docker run -i --rm tng-sdk-project pytest -v
