#! /usr/bin/env python
import unittest2
from result import Result

class ResultTestCase(unittest2.TestCase):
  def setUp(self):
    self.status_fail = """{
      "status": {
        "message": "Unknown image id",
        "code": -2601
      },
      "image": null
    }"""
    self.status_success = """{
      "status":
      {
        "message": "No error",
        "code": 0
      },
      "image": {
        "keywords": [],
        "score": 0,
        "id": "4e8f9cc37b9aa143bf00120f",
        "result_info": ""
      }
    }"""

  def testInitSuccess(self):
    result = Result(self.status_success)
    self.assertEqual("No error", result.status_message)
    self.assertEqual(0, result.status_code)
    self.assertIsNotNone(result.image)
    self.assertEqual([], result.image.keywords)
    self.assertEqual(0, result.image.score)
    self.assertEqual("4e8f9cc37b9aa143bf00120f", result.image.id)
    self.assertIsNone(result.image.result_info)

  def testInitFail(self):
    result = Result(self.status_fail)
    self.assertEqual("Unknown image id", result.status_message)
    self.assertEqual(-2601, result.status_code)
    self.assertIsNone(result.image)

  def testToString(self):
    result = Result(self.status_success)
    image_string  = "%s" % result.image
    result_string = "%s" % result

if __name__ == "__main__":
  unittest2.main()
