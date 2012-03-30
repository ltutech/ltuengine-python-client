import urllib, urllib2, urlparse, os

from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
from result import Result

# Register the streaming http handlers with urllib2
register_openers()

class BaseClient(object):
  """Base class from which ModifyClient and QueryClient inherit.

  This class contains basic methods for accessing the API.
  """

  def __init__(self, application_key, server_url):
    """Constructor
    Args:
      application_key: authentication key provided by the application.
      server_url: complete http url to the OnDemand server.
    """
    self.application_key = application_key
    self.server_url      = server_url

  def get_url(self, service):
    """Combine a service name and the server url to produce the service url.
    """
    return urlparse.urljoin(self.server_url, service)

  @classmethod
  def get_file(cls, f):
    """Return a file object in 'rb' mode, from either a file path or a file
    object.

    In case the input image is a file object, it is the user's responsibility
    for closing it after use.

    Args:
      f: either a path to a file or a file instance
    Returns:
      a file object.

    """
    if isinstance(f, str):
      return open(f, 'rb')
    elif isinstance(f, file):
      return f
    else:
      raise ValueError("Image object of unknown type: %s" % type(f))

  def get_data(self, params={}):
    """Return appropriate HTTP POST parameters and headers

    The application key is automatically added.

    Args:
      params: a dictionary with service-specific parameters
    Returns:
      data, headers to be passed to urllib2.Request constructor.

    """
    data      = [("application_key", self.application_key)]
    multipart = False
    for key, val in params.iteritems():
      if val is not None:
        if isinstance(val, file):
          multipart = True
        if isinstance(val, (list, tuple, set)):
          for v in val:
            data.append((key, v));
        else:
          data.append((key, val))

    if multipart:
      datagen, headers = multipart_encode(data)
    else:
      datagen = urllib.urlencode(data)
      headers = {}
    return datagen, headers

  def check_status(self):
    """Check that this client can successfully access your application.

    Logs advice on actions to take as warnings in case of wrong status.
    """
    result = self.get_application_status()
    if result.status_code >= 0:
      return True
    else:
      return False

  def open_service(self, service, params={}):
    """Open corresponding API service with appropriate parameters.

    Args:
      service: service name, e.g: GetApplicationStatus
      params: a dictionary of arguments to be passed to the service
    Returns:
      The response content.
    """
    data, headers = self.get_data(params=params)
    url           = self.get_url(service)
    request       = urllib2.Request(url, data, headers)
    return urllib2.urlopen(request).read()

  def get_application_status(self):
    """Check the application status.

    Example:
      result = client.get_application_status()
      if(result.status_code < 0):
        raise Exception(result.status_message)

    """
    result = self.open_service("GetApplicationStatus")
    return Result(result)

  def get_image_by_id(self, image_id):
    """Check if a an image exists in the database"""
    result = self.open_service("GetImageById", params={"image_id": image_id})
    return Result(result)

class QueryClient(BaseClient):
  """Read-only client.
  """

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

  def search_image_by_upload(self, image):
    """Image retrieval based on a image stored on disk

    Args:
      image: can be either an image path or a file object.

    Example:
      image_path = "/home/user/image.jpg"
      with open(image_path, 'rb') as image:
        result = client.search_image_by_upload(image)

    """
    result = self.open_service("SearchImageByUpload",
                               params={"image_content": self.get_file(image)})
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
  """Client with write capabilities.
  """

  DEFAULT_MODIFY_URL = "https://api.ltu-engine.com/v2/ltumodify/json/"

  def __init__(self, application_key, server_url = None):
    """Constructor
    Args:
      application_key: authentication key provided by the application.
      server_url: complete http url to the OnDemand server. If it not
                  specified, it will default to the production environment url.
    """
    if not server_url:
      server_url = ModifyClient.DEFAULT_MODIFY_URL
    BaseClient.__init__(self, application_key, server_url)

  def add_image(self, image_id, image, keywords=[]):
    """Add an image to the database

    Args:
      image_id: any unique identifier
      image:    can be either a path or a file object
      keywords: a keyword strings iterable.
    """
    result = self.open_service("AddImage", params={"image_id": image_id,
                                                   "image_content": self.get_file(image),
                                                   "keywords": keywords})
    return Result(result)

  def delete_image(self, image_id):
    """Remove an image from the database"""
    result = self.open_service("DeleteImage", params={"image_id": image_id})
    return Result(result)

