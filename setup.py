#!/usr/bin/env python
from setuptools import setup

VERSION = "1.1"
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
  'install_requires': ['unittest2==1.1.0',
                       'mock==2.0.0',
                       'requests==2.10.0'],
  'author': "LTU technologies",
  'author_email': "support@ltutech.com",
  'maintainer': "LTU technologies",
  'maintainer_email': "support@ltutech.com",
  'license': "LICENSE",
  'version': VERSION,
}


if __name__ == "__main__":
  setup(**PARAMETERS)
