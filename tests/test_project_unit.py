import pytest
import os
import shutil
import yaml
import tngsdk.cli as cli
from tngsdk.project.project import Project

#TEST:START Test if get descriptor functions work properly
example_project = Project.load_project('../example-project')
example_project.status()

vnfds = example_project.get_vnfds()
assert vnfds == ['tango_vnfd0.yml']

nsds = example_project.get_nsds()
assert nsds == ['tango_nsd.yml']

tstds = example_project.get_tstds()
assert tstds == ['test-descriptor-example.yml']
#TEST:END 