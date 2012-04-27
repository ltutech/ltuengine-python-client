#! /usr/bin/env python
import unittest2, os, mock

from result import Result
from client import BaseClient, QueryClient, ModifyClient

class ClientTestCase(unittest2.TestCase):

  def setUp(self):
    self.application_key = "123456"
    self.server_url      = "http://ltutech.com"
    self.query_client    = QueryClient(application_key=self.application_key)
    self.modify_client   = ModifyClient(application_key=self.application_key)
    self.image_path       = os.path.join(os.path.abspath(os.path.dirname(__file__)), 
                                        "../../fixtures/kill-bill-vol-1.jpg")

    # Query results
    self.search_image_result = """{"images": [{"keywords": [], "score": 0.10410962999999999, "id": "4ea5cc294f13c137cc000063", "result_info": "{\\n  \\"category\\" : \\"LOCALMATCHING\\",\\n  \\"query\\" : \\n  {\\n    \\"originalDimensions\\" : [500, 718],\\n    \\"resizedDimensions\\" : [356, 512],\\n    \\"matchingBox\\" : \\n    {\\n      \\"topLeftPoint\\" : [0.0197, 0.0449],\\n      \\"bottomRightPoint\\" : [0.9663, 0.9922]\\n    }\\n  },\\n  \\"reference\\" : \\n  {\\n    \\"originalDimensions\\" : [1000, 1435],\\n    \\"resizedDimensions\\" : [356, 512],\\n    \\"matchingBox\\" : \\n    {\\n      \\"topLeftPoint\\" : [0.0197, 0.0449],\\n      \\"bottomRightPoint\\" : [0.9663, 0.9922]\\n    }\\n  },\\n  \\"homography\\" : \\n  {\\n    \\"source\\" : \\"reference\\",\\n    \\"destination\\" : \\"query\\",\\n    \\"coefficients\\" : [1.0005, 0.0005, -0.0004, -0.0003, 1.0009, -0.0001, -0.0000, 0.0008, 1.0000]\\n  }\\n}"}, {"keywords": [], "score": 0.18547931300000001, "id": "4ea60983a34d4b41fd000065", "result_info": "{\\n  \\"category\\" : \\"LOCALMATCHING\\",\\n  \\"query\\" : \\n  {\\n    \\"originalDimensions\\" : [500, 718],\\n    \\"resizedDimensions\\" : [356, 512],\\n    \\"matchingBox\\" : \\n    {\\n      \\"topLeftPoint\\" : [0.0197, 0.0449],\\n      \\"bottomRightPoint\\" : [0.9663, 0.9238]\\n    }\\n  },\\n  \\"reference\\" : \\n  {\\n    \\"originalDimensions\\" : [1000, 1435],\\n    \\"resizedDimensions\\" : [356, 512],\\n    \\"matchingBox\\" : \\n    {\\n      \\"topLeftPoint\\" : [0.0169, 0.0449],\\n      \\"bottomRightPoint\\" : [0.9663, 0.9238]\\n    }\\n  },\\n  \\"homography\\" : \\n  {\\n    \\"source\\" : \\"reference\\",\\n    \\"destination\\" : \\"query\\",\\n    \\"coefficients\\" : [0.9990, 0.0005, -0.0003, -0.0002, 0.9990, 0.0006, 0.0000, 0.0000, 1.0000]\\n  }\\n}"}], "status": {"message": "No error", "code": 0}, "nb_results_found": 2}"""
    self.get_application_status_result = """{"status": {"message": "No error", "code": 0}, "nb_loaded_images": 32995}"""
    self.add_image_result = """{"status": {"message": "Image added to the reference database", "code": 0}, "task_id": 0}"""
    self.add_image_error_result = """{"status": {"message": "status='-1404' status_message='Invalid chars in keyword'", "code": -1404}, "task_id": 0}"""
    self.delete_image_result = """{"status": {"message": "Image deleted from the reference database", "code": 0}, "task_id": 0}"""

  def testInit(self):
    client = BaseClient(self.application_key, self.server_url)
    self.assertEqual(self.application_key, client.application_key)
    self.assertEqual(self.server_url,      client.server_url)

    query_client = QueryClient(self.application_key, self.server_url)
    self.assertEqual(query_client.application_key, client.application_key)
    self.assertEqual(query_client.server_url,      client.server_url)

  def testSearchImageByUpload(self):
    self.query_client.open_service = mock.MagicMock(return_value=self.search_image_result)
    result = self.query_client.search_image(self.image_path)

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

  def testAddImage(self):
    # Success
    self.modify_client.open_service = mock.MagicMock(return_value=self.add_image_result)
    result = self.modify_client.add_image("myimage", self.image_path)
    self.assertEqual(0, result.status_code)

    # Error
    self.modify_client.open_service = mock.MagicMock(return_value=self.add_image_error_result)
    result = self.modify_client.add_image("myimage", self.image_path, keywords=";*()[]")
    self.assertEqual(-1404, result.status_code)
    self.assertEqual("status='-1404' status_message='Invalid chars in keyword'", result.status_message)

  def testDeleteImage(self):
    self.modify_client.open_service = mock.MagicMock(return_value=self.delete_image_result)
    result = self.modify_client.delete_image("myimage")
    self.assertEqual(0, result.status_code)
    self.assertEqual("Image deleted from the reference database", result.status_message)

  def testCheck(self):
    self.query_client.get_application_status = mock.MagicMock(return_value=Result(self.get_application_status_result))
    self.assertTrue(self.query_client.check_status())

if __name__ == "__main__":
  unittest2.main()
