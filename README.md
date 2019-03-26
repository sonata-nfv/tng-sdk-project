[![Join the chat at https://gitter.im/sonata-nfv/Lobby](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/sonata-nfv/Lobby)
[![Build Status](https://jenkins.sonata-nfv.eu/buildStatus/icon?job=tng-sdk-project-pipeline/master)](https://jenkins.sonata-nfv.eu/job/tng-sdk-project-pipeline/job/master/)

<p align="center"><img src="https://github.com/sonata-nfv/tng-api-gtw/wiki/images/sonata-5gtango-logo-500px.png" /></p>

# tng-sdk-project

This repository contains the `tng-sdk-project` component that is part of the European H2020 project [5GTANGO](http://www.5gtango.eu) NFV SDK. This component is responsible to manage network service workspaces and projects on the developer's machine. It allows preparing 5GTANGO projects containing service descriptions, for example. These projects are prepared for packaging and future use by other components.

The seed code of this component is based on the `son-cli` toolbox that was developed as part of the European H2020 project [SONATA](http://sonata-nfv.eu).

## Installation

Requires Python 3.5+ and `setuptools`.

For simple, automatic installation and usage:

```bash
$ pip install git+https://github.com/sonata-nfv/tng-sdk-project.git
```

Alternatively, for obtaining the source code, installation, and development:

```bash
$ git clone https://github.com/sonata-nfv/tng-sdk-project.git
$ cd tng-sdk-project
$ sudo python3 setup.py install
```

It is a good practice to first create a new virtual environment in which all 5GTANGO SDK tools can be installed. You can do this as follows:

```sh
# get the path to your Python3 installation
which python3

# create a new virtualenv
virtualenv -p <path/to/python3> venv

# activate the virtualenv
source venv/bin/activate
```

## Usage

### CLI
#### Workspace
To start working, you need a workspace that holds your configuration files. The default location is `~/.tng-workspace/`, but it may be at any location and there can also be multiple workspaces.

```bash
$ tng-workspace       # initializes a new workspace at the default location
$ tng-workspace --workspace path/to/workspace     # inits a workspace at a custom location
```

#### Project managament
Once you have a workspace, you can create projects with the `tng-project` command.
You can also add or remove files from the project (wildcards allowed) or check the project status.

```bash
$ tng-project -p path/to/project                # creates a new project at the specified path
$ tng-project -p path/to/project --add file1    # adds file1 to the project.yml
$ tng-project -p path/to/project --add file1 --type text/plain  # adds file1 with explicit MIME type
$ tng-project -p path/to/project --remove file1 # removes file1 from the project.yml
$ tng-project -p path/to/project --status       # shows project overview/status
```

The `--workspace` option allows to specify a workspace at a custom location. Otherwise, the workspace at the default location is used.
For both `tng-workspace` and `tng-project` the option `--debug` makes the output more verbose.

Since the structure of projects and descriptors changed from SONATA (v3.1) to 5GTANGO (v4.0), `tng-project` also provides a command to automatically translate old to new projects.
For more information see the [corresponding wiki page](https://github.com/sonata-nfv/tng-sdk-project/wiki/Translating-SONATA-SDK-projects-to-5GTAGNO-SDK-projects).

```bash
$ tng-project -p path/to/old-project --translate   # translates the project to the new structure
```

#### Descriptor generation (CLI)
This tool also includes a CLI for descriptor generation. 
Its functionality is mostly consistent with the [GUI version](https://github.com/sonata-nfv/tng-sdk-descriptorgen) but my be preferrable to advanced users.

The descriptor generator is integrated in the project management tool 
such that additional arguments are passed to the descriptor generator
and are used to generate suitable descriptors in a new project:

```bash
$ tng-project -p path/to/project --author abc --vnfs 2 \  
  --image_names img1 img2 --image_types docker docker     # creates a new project with descriptors for 2 VNFs with the specified author and images
```

The descriptorgen CLI can also be used separately as follows:

```bash
$ tng-descriptorgen --author author.name --vnfs 3   # generate NSD and VNFDs for service with 3 VNFs
$ tng-descriptorgen --author author.name --vnfs 2 \
  --image_names img1 img2 --image_types docker docker  # generate descriptors for 2 VNFs with specific images
$ tng-descriptorgen --tango -o tango-project        # generate only 5GTANGO descriptors in a folder "tango-project"
$ tng-descriptorgen --osm -o osm-project            # generate only OSM descriptors in a folder "osm-project"
```

For more information, use `tng-descriptorgen -h`.


### Service mode with REST API

**Run on bare metal:**

```bash
# terminal 1
$ tng-project -s    # starts the tool in service mode (running forever)
```

This will start the tool in service mode running in the terminal forever until stopped with Ctrl+C.

**Run in Docker container:**

```bash
pipeline/build/build.sh
docker run --rm -d -p 5098:5098 --name tng-sdk-project registry.sonata-nfv.eu:5000/tng-sdk-project
```

This will run the tool in service mode in a detached Docker container, i.e., in the background.
See the [wiki page on Docker deployment](https://github.com/sonata-nfv/tng-sdk-project/wiki/docker-deployment) for additional details.

The Docker image is also available on [DockerHub](https://hub.docker.com/r/sonatanfv/tng-sdk-project):

```bash
docker pull sonatanfv/tng-sdk-project
```

**Calling the REST API**

Showing, adding, deleting projects:
```bash
# terminal 2
$ curl -X GET localhost:5098/api/v1/projects             # show all projects
$ curl -X POST localhost:5098/api/v1/projects            # create a new project
$ curl -X POST localhost:5098/api/v1/projects \
-d author=alice -d vendor=eu.tango -d vnfs=3             # new project with custom-generated descriptors
$ curl -X POST localhost:5098/api/v1/projects \
-d vnfs=2 -d image_names="img1 img2"                     # you can specify image names/types as white space-separated list in quotation marks ("", not ''!) 
$ curl -X GET localhost:5098/api/v1/projects/{uuid}      # show details of the specified project
$ curl -X DELETE localhost:5098/api/v1/projects/{uuid}   # delete the specified project
```

Showing, adding, deleting project files:
```bash
# terminal 2
$ curl -X GET localhost:5098/api/v1/projects/{uuid}/files   # show files of the specified project
$ curl -X POST localhost:5098/api/v1/projects/{uuid}/files \
    -H "Content-Type: multipart/form-data" \
    -F file="@requirements.txt"                             # add new file to the project
$ curl -X POST localhost:5098/api/v1/projects/{uuid}/files \
    -H "Content-Type: multipart/form-data" \
    -F file="@LICENSE" -F file_type="text/plain"            # add new file with specific MIME type
$ curl -X DELETE localhost:5098/api/v1/projects/{uuid}/files \
    -d filename="requirements.txt"                          # remove the specified file
```

*Note:* If using the Docker deployment, replace `localhost` with the IP address of the Docker host.

**REST API Swagger Specification**

Find the API specification [here](http://swagger.peuster.de/?url=https://raw.githubusercontent.com/sonata-nfv/tng-sdk-project/master/docs/rest_api.json).

## Documentation

See the [wiki](https://github.com/sonata-nfv/tng-sdk-project/wiki) for further documentation and details.

## Dependencies

tng-sdk-project only depends on Python packages, which are listed in and can be installed through [`setup.py`](setup.py).

## Development

To contribute to the development of this 5GTANGO component, you may use the very same development workflow as for any other 5GTANGO Github project. That is, you have to fork the repository and create pull requests.

### Setup development environment

```bash
$ python setup.py develop
```

### CI Integration

All pull requests are automatically tested by Jenkins and will only be accepted if no test is broken.

### Run tests manually

You can also run the test manually on your local machine. To do so, you need to do:

```bash
$ pytest -v
$ pycodestyle .
```

## License

This 5GTANGO component is published under Apache 2.0 license. Please see the LICENSE file for more details.

---
#### Lead Developers

The following lead developers are responsible for this repository and have admin rights. They can, for example, merge pull requests.

- Stefan Schneider ([@stefanbschneider](https://github.com/stefanbschneider))
- Manuel Peuster ([@mpeuster](https://github.com/mpeuster))

#### Feedback-Chanel

* Please use the GitHub issues to report bugs.
