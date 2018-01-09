import logging
import os
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import sys

import json

from ltu.engine.result import Result, FICResult

# disable some requests warning and info messages
requests.packages.urllib3.disable_warnings()
logger = logging.getLogger('__main__')
logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.ERROR)

class BaseClient(object):
  """Base class from which ModifyClient and QueryClient inherit.

  This class contains basic methods for accessing the API.
  """

  def __init__(self, application_key, server_url):
    """Constructor
    Args:
      application_key:  authentication key provided by the application.
      server_url:       complete http url to the OnDemand server.
    """
    self.application_key = application_key
    self.base_server_url = server_url.rstrip('/')
    self.server_url = self.base_server_url
    # improve connection rebustness with retries
    self.session = requests.Session()
    retries = Retry(total=5,
                    backoff_factor=0.1,
                    status_forcelist=[ 500, 502, 503, 504 ])
    self.session.mount('http://', HTTPAdapter(max_retries=retries))
    self.session.mount('https://', HTTPAdapter(max_retries=retries))

  def _connect(self, url_list=[]):
    """Connect to remote server using a list of possible API paths.
       It will try them all to perform auto-discovery of the right URL.
    """
    logger.info('Auto discovering API path with base server URL: %s' % self.base_server_url)
    full_urls = [self.base_server_url] + ["%s%s" % (self.base_server_url, url) for url in url_list]
    # Test all API paths
    for url in full_urls:
      try:
        self.server_url = url
        logger.debug('Testing URL: %s' % self.server_url)
        status = self.check_status()
        if status:
          logger.info('API path found at: %s' % url)
          return True
      except Exception as e:
        logger.critical("Could not connect to your application: %s", e)
        sys.exit(-1)

  def get_url(self, service):
    """Combine a service name and the server url to produce the service url.
    """
    logger.debug("Joining URLs %s and %s" % (self.server_url, service))
    url = requests.compat.urljoin("%s/" % self.server_url, service)
    logger.debug("Final URL: %s" % url)
    return url

  def get_data(self, params={}):
    """Return appropriate HTTP POST parameters and optional file

    The application key is automatically added.

    Args:
      params: a dictionary with service-specific parameters
    Returns:
      filtered_params, files to be passed to requests.
    """
    data = [("application_key", self.application_key)]
    for key, val in params.items():
      if val is not None:
        if isinstance(val, (list, tuple, set)):
          for v in val:
            data.append((key, v));
        else:
          data.append((key, val))

    return data

  def check_status(self):
    """Check that this client can successfully access your application.

    Logs advice on actions to take as warnings in case of wrong status.
    """
    result = self.get_application_status()
    if result.status_code == 0:
      return True
    else:
      return False

  def open_service(self, service, params={}, files=None):
    """Open corresponding API service with appropriate parameters.

    Args:
      service: service name, e.g: GetApplicationStatus
      params: a dictionary of arguments to be passed to the service
    Returns:
      The response content.
    """
    data    = self.get_data(params)
    url     = self.get_url(service)
    logger.debug("Sending '%s' request to: %s" % (service, url))
    response = self.session.post(url, data=data, files=files, verify=False)
    # check that we do not have HTTP error first
    response.raise_for_status()
    return response.text

  def get_application_status(self):
    """Check the application status.

    Example:
      result = client.get_application_status()
      if(result.status_code < 0):
        raise Exception(result.status_message)
    """
    result = self.open_service("GetApplicationStatus")
    return Result(result)

  def get_image(self, image_id):
    """Search for an image based on its id."""
    result = self.open_service("GetImageById", params={"image_id": image_id})
    return Result(result)

class QueryClient(BaseClient):
  """Client that can run searches on an LTU Engine application."""

  DEFAULT_QUERY_URL = "https://api.ltu-engine.com/v2/ltuquery/json/"

  def __init__(self, application_key, server_url=None):
    """Constructor

    Args:
      application_key: authentication key provided by the application.
      server_url: complete http url to the OnDemand server. If it not
                  specified, it will default to the default url.
    """
    logger.info('Starting query client...')
    self.server_url = server_url
    if not server_url:
      self.server_url = QueryClient.DEFAULT_QUERY_URL
    BaseClient.__init__(self, application_key, self.server_url)
    url_list = [':8080/api/v2.0/ltuquery/json/',
                '/api/v2.0/ltuquery/json/',
                ':8080/api/v2/ltuquery/json/',
                '/api/v2/ltuquery/json/',
    ]
    BaseClient._connect(self, url_list)

  def search_image(self, image, params={}):
    """Image retrieval based on a image stored on disk

    Args:
      image: path to image file.
    """
    with open(image, 'rb') as img:
      result = self.open_service("SearchImageByUpload",
                                 files={"image_content": img},
                                 params=params)
    return Result(result)

  # TODO test this
  def search_image_by_keywords(self, keywords, starting_index=None,
                               nb_results=None, ids_list=None):
    """Search all images with associated keywords.

    Args:
      keywords: an iterator on a keyword strings
    """
    result = self.open_service("SearchImageByKeywords",
                               params={"keywords": keywords, "starting_index":
                                       starting_index, "nb_results":
                                       nb_results, "ids_list": ids_list})
    return Result(result)

  def fine_image_comparison(self, reference_image, query_image):
    """Compare two images using the Fine Image Comparison.
    NOTE: This features works only on application with Fine
    Image Comparison enabled. Contact the support for more
    information.

    Args:
      reference_image: path to reference image file.
      query_image: path to query image file.
    """
    try:
        files = {}
        files['reference_image'] = open(reference_image, 'rb')
        files['query_image'] = open(query_image, 'rb')
    except Exception as e:
        logger.critical('Could not open one of the input files: {}'.format(e))
        sys.exit(-1)

    result = self.open_service("FineComparison", files=files)
    return FICResult(result)


class ModifyClient(BaseClient):
  """Client that can modify an LTU Engine application, e.g: by adding and
  removing images."""

  DEFAULT_MODIFY_URL = "https://api.ltu-engine.com/v2/ltumodify/json/"

  def __init__(self, application_key, server_url = None):
    """Constructor
    Args:
      application_key:  authentication key provided by the application.
      server_url:       complete http url to the OnDemand server. If it is not
                        specified, it will default to the default url.
    """
    logger.info('Starting modify client...')
    if not server_url:
      server_url = ModifyClient.DEFAULT_MODIFY_URL
    BaseClient.__init__(self, application_key, server_url)
    url_list = [':7789/api/v2.0/ltumodify/json/',
                '/api/v2.0/ltumodify/json/',
                ':7789/api/v2/ltumodify/json/',
                '/api/v2/ltumodify/json/',
    ]
    BaseClient._connect(self, url_list)


  def add_image(self, image, image_id=None, keywords=[]):
    """Add an image to the database

    Args:
      image:    path to image file
      image_id: any unique identifier
      keywords: an iterator on a keyword strings
    """
    if not image_id:
      image_id = os.path.basename(image)
    with open(image, 'rb') as img:
      result = self.open_service("AddImage",
                                 params={"image_id": image_id, "keywords": keywords},
                                 files={"image_content": img})
    return Result(result)

  def delete_image(self, image_id):
    """Remove an image from the database"""
    result = self.open_service("DeleteImage", params={"image_id": image_id})
    return Result(result)

  def delete_imagefile(self, file):
    image_id = os.path.basename(file)
    return self.delete_image(image_id)
