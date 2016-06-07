import os
import requests

from result import Result

# Register the streaming http handlers with requests

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
    self.server_url      = server_url

  def get_url(self, service):
    """Combine a service name and the server url to produce the service url.
    """
    return requests.compat.urljoin(self.server_url, service)

  def get_data(self, params={}):
    """Return appropriate HTTP POST parameters and optional file

    The application key is automatically added.

    Args:
      params: a dictionary with service-specific parameters
    Returns:
      filtered_params, files to be passed to requests.
    """
    data = [("application_key", self.application_key)]
    print(params)
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
    request = requests.post(url, data=data, files=files)
    return request.text

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
    if not server_url:
      server_url = QueryClient.DEFAULT_QUERY_URL
    BaseClient.__init__(self, application_key, server_url)

  def search_image(self, image):
    """Image retrieval based on a image stored on disk

    Args:
      image: path to image file.
    """
    with open(image, 'rb') as img:
      result = self.open_service("SearchImageByUpload",
                                 files={"image_content": img})
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
    if not server_url:
      server_url = ModifyClient.DEFAULT_MODIFY_URL
    BaseClient.__init__(self, application_key, server_url)

  def add_image(self, image_id, image, keywords=[]):
    """Add an image to the database

    Args:
      image_id: any unique identifier
      image:    path to image file
      keywords: an iterator on a keyword strings
    """
    with open(image, 'rb') as img:
      result = self.open_service("AddImage",
                                 params={"image_id": image_id, "keywords": keywords},
                                 files={"image_content": img})
    return Result(result)

  def delete_image(self, image_id):
    """Remove an image from the database"""
    result = self.open_service("DeleteImage", params={"image_id": image_id})
    return Result(result)

