import json
import base64

class Result(object):
  """Parse the server JSON response to produce a result.
  """

  def __init__(self, json_result):
    """Parse a JSON result as produced by the OnDemand API.

    Args:
      json_result: JSON-formatted string
    """

    data    = json.loads(json_result)

    # Parsing status
    status = data.get("status", {})
    self.status_message = status.get("message", "")
    self.status_code    = status.get("code", -1)

    # Parsing image
    image_dict = data.get("image")
    self.image = Image(image_dict) if image_dict else None

    # Parsing images
    self.images = []
    for image in data.get("images", []):
      self.images.append(Image(image))

    # Result stats
    self.nb_results_found = data.get("nb_results_found")
    self.nb_loaded_images = data.get("nb_loaded_images")

    # Task status
    self.task_id = None
    self.task_status         = ""
    self.task_status_code    = None
    self.task_status_message = ""


  def __str__(self):
    """String convertor"""

    res = """
Status Code    : %d
Status Message : %s""" % (self.status_code, self.status_message)
    if self.nb_loaded_images:
      res += """
Loaded Images  : %d""" % self.nb_loaded_images
    if self.task_id:
      res += """
Task Id        : %d""" % self.task_id
    if self.task_status_code != None:
      res += """
Task Status    : %s
Task Code      : %d
Task Message   : %s""" % (self.task_status, self.task_status_code,
                          self.task_status_message)
    if self.nb_results_found != None:
      res += """
Nb results     : %d""" % self.nb_results_found
    if self.image:
      res += '\n' + str(self.image)
    if self.images:
      res += """
------------------------------------------
Results:
------------------------------------------
""" + '\n-----------------------------------------\n'.join(map(str, self.images))
    return res


class Image:
  def __init__(self, image_dict):
    self.data = image_dict
    self.keywords    = image_dict.get("keywords", [])
    self.score       = image_dict.get("score", 0.)
    self.id          = image_dict.get("id", "")
    result_info      = image_dict.get("result_info")
    self.result_info = json.loads(result_info) if result_info else None

  def __str__(self):
    return """Id         : %s
Score      : %f
Keywords   : %s
Result Info: %s""" % (self.id, self.score, ', '.join(self.keywords), self.result_info)

  def save_json(self, filepath):
      """Dump original data into a json file.
      """
      with open(filepath, 'w') as outfile:
        json.dump(self.data, outfile, indent=2)


class FICResult(object):
  """Parse the server JSON response to produce a Fine Image Comparison result.
  """

  def __init__(self, json_result):
    """Parse a JSON result as produced by the OnDemand API.

    Args:
      json_result: JSON-formatted string
    """

    data = json.loads(json_result)

    # Parsing status
    status = data.get("status", {})
    self.status_message = status.get("message", "")
    self.status_code    = status.get("code", -1)

    # Parsing reference image
    self.reference_image_data = data.get("ref_image")

    # Parsing query reference image
    self.query_image_data = data.get("query_image")

    # Result stats
    self.score = data.get("score")

  def __str__(self):
    """String convertor"""

    res = """
Status Code    : %d
Status Message : %s""" % (self.status_code, self.status_message)
    res += """
Score     : %d""" % self.score
    return res

  def _save_image(self, path, data):
    with open(path, 'wb') as img:
        img.write(base64.b64decode(data))

  def save_query(self, path):
    """Save query image with Fine Image Comparison
    highlighted areas.

    Args:
      path: destination path
    """
    self._save_image(path, self.query_image_data)

  def save_reference(self, path):
    """Save reference image with Fine Image Comparison
    highlighted areas.

    Args:
      path: destination path
    """
    self._save_image(path, self.reference_image_data)