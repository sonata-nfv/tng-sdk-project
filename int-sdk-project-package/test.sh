#!/bin/bash
set -e

# install required packages
apt-get install -y git python3 python3-setuptools
    
# install tng-sdk-project
git clone https://github.com/sonata-nfv/tng-sdk-project.git
cd tng-sdk-project && python3 setup.py develop & cd ..

# install tng-sdk-package
git clone https://github.com/sonata-nfv/tng-sdk-package.git
cd tng-sdk-package && python3 setup.py install & cd ..

# create a workspace
printf "Configuring workspace"
tng-workspace

# create a project
printf "Creating project"
tng-project -p p1

# create and add a text file
printf "Create and add test file"
echo "test text file" > p1/test.txt
tng-project -p p1 --add p1/test.txt
tng-project -p p1 --status

# package the project
printf "Package the project"
tng-package -p p1

# unpackage the project again and check its status
printf "Unpackage the project"
tng-package -u eu.5gtango.5gtango-project-sample.0.1.tgo
tng-project -p eu.5gtango.5gtango-project-sample.0.1 --status

# test packaging and unpackaging of tng-schema examples
git clone https://github.com/sonata-nfv/tng-schema.git
cd tng-schema/package-specification/
tng-package -p example-projects/5gtango-ns-project-example
tng-package -u example-projects/eu.5gtango.ns-package-example.0.1.tgo
