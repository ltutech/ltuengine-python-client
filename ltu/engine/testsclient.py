#! /usr/bin/env python
import unittest2, os, mock

from result import Result
from client import BaseClient, QueryClient

class ClientTestCase(unittest2.TestCase):

  def setUp(self):
    self.application_key = "123456"
    self.server_url      = "http://ltutech.com"
    self.query_client          = QueryClient(application_key=self.application_key)
    self.imagePath = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                   "../../fixtures/kill-bill-vol-1.jpg")
    self.search_image_by_upload_result = """{"images": [{"keywords": [], "score": 0.10410962999999999, "id": "4ea5cc294f13c137cc000063", "result_info": "{\\n  \\"category\\" : \\"LOCALMATCHING\\",\\n  \\"query\\" : \\n  {\\n    \\"originalDimensions\\" : [500, 718],\\n    \\"resizedDimensions\\" : [356, 512],\\n    \\"matchingBox\\" : \\n    {\\n      \\"topLeftPoint\\" : [0.0197, 0.0449],\\n      \\"bottomRightPoint\\" : [0.9663, 0.9922]\\n    }\\n  },\\n  \\"reference\\" : \\n  {\\n    \\"originalDimensions\\" : [1000, 1435],\\n    \\"resizedDimensions\\" : [356, 512],\\n    \\"matchingBox\\" : \\n    {\\n      \\"topLeftPoint\\" : [0.0197, 0.0449],\\n      \\"bottomRightPoint\\" : [0.9663, 0.9922]\\n    }\\n  },\\n  \\"homography\\" : \\n  {\\n    \\"source\\" : \\"reference\\",\\n    \\"destination\\" : \\"query\\",\\n    \\"coefficients\\" : [1.0005, 0.0005, -0.0004, -0.0003, 1.0009, -0.0001, -0.0000, 0.0008, 1.0000]\\n  }\\n}"}, {"keywords": [], "score": 0.18547931300000001, "id": "4ea60983a34d4b41fd000065", "result_info": "{\\n  \\"category\\" : \\"LOCALMATCHING\\",\\n  \\"query\\" : \\n  {\\n    \\"originalDimensions\\" : [500, 718],\\n    \\"resizedDimensions\\" : [356, 512],\\n    \\"matchingBox\\" : \\n    {\\n      \\"topLeftPoint\\" : [0.0197, 0.0449],\\n      \\"bottomRightPoint\\" : [0.9663, 0.9238]\\n    }\\n  },\\n  \\"reference\\" : \\n  {\\n    \\"originalDimensions\\" : [1000, 1435],\\n    \\"resizedDimensions\\" : [356, 512],\\n    \\"matchingBox\\" : \\n    {\\n      \\"topLeftPoint\\" : [0.0169, 0.0449],\\n      \\"bottomRightPoint\\" : [0.9663, 0.9238]\\n    }\\n  },\\n  \\"homography\\" : \\n  {\\n    \\"source\\" : \\"reference\\",\\n    \\"destination\\" : \\"query\\",\\n    \\"coefficients\\" : [0.9990, 0.0005, -0.0003, -0.0002, 0.9990, 0.0006, 0.0000, 0.0000, 1.0000]\\n  }\\n}"}], "status": {"message": "No error", "code": 0}, "nb_results_found": 2}"""
    self.get_application_status_result = """{"status": {"message": "No error", "code": 0}, "nb_loaded_images": 32995}"""
    # TODO test these
    self.addImageResult = """{"status": {"message": "Image added to the reference database", "code": 0}, "task_id": 0}"""
    self.addImageErrorResult = """{"status": {"message": "status='-1404' status_message='Invalid chars in keyword'", "code": -1404}, "task_id": 0}"""
    self.deleteImageResult = """{"status": {"message": "Image deleted from the reference database", "code": 0}, "task_id": 0}"""

  def testInit(self):
    client = BaseClient(self.application_key, self.server_url)
    self.assertEqual(self.application_key, client.application_key)
    self.assertEqual(self.server_url,      client.server_url)

    query_client = QueryClient(self.application_key, self.server_url)
    self.assertEqual(query_client.application_key, client.application_key)
    self.assertEqual(query_client.server_url,      client.server_url)

  def testSearchImageByUpload(self):
    self.query_client.open_service = mock.MagicMock(return_value=self.search_image_by_upload_result)
    with open(self.imagePath, 'rb') as f:
      result = self.query_client.search_image_by_upload(open(self.imagePath, 'rb'))

    self.assertEqual(2, len(result.images))
    self.assertEqual(2, result.nb_results_found)

    self.assertIsNotNone(result.images[0].result_info)
    self.assertEqual("LOCALMATCHING", result.images[0].result_info["category"])
    self.assertEqual([356, 512], result.images[0].result_info["query"]["resizedDimensions"])
    self.assertEqual("No error", result.status_message)

  def testGetApplicationStatus(self):
    self.query_client.open_service = mock.MagicMock(return_value=self.get_application_status_result)
    result = self.query_client.get_application_status()
    self.assertEqual(32995, result.nb_loaded_images)

  def testCheck(self):
    self.query_client.get_application_status = mock.MagicMock(return_value=Result(self.get_application_status_result))
    self.assertTrue(self.query_client.check_status())

if __name__ == "__main__":
  unittest2.main()
