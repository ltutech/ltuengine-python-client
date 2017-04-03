#!/usr/bin/env python
from setuptools import setup

VERSION = "1.2"
DESCRIPTION = "LTU Engine API Python client."

PARAMETERS = {
  'name': 'ltuengine-python-client',
  'description': DESCRIPTION,
  'packages': [
    'ltu.engine',
    'ltu'
  ],
  'namespace_packages': ['ltu'],
  'package_dir': {
    'ltu.engine': 'ltu/engine',
    'ltu': 'ltu'
  },
  'install_requires': ['begins==0.9',
                       'coloredlogs==5.1.1',
                       'mock==2.0.0',
                       'requests==2.10.0',
                       'tqdm==4.11.0',
                       'unittest2==1.1.0'],
  'author': "JASTEC France",
  'author_email': "support@jastec.fr",
  'maintainer': "JASTEC France",
  'maintainer_email': "support@jastec.fr",
  'license': "LICENSE",
  'version': VERSION,
}


if __name__ == "__main__":
  setup(**PARAMETERS)
