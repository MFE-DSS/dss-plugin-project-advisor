import unittest
from unittest.mock import MagicMock
from python-lib.project_advisor.assessments.checks.project_checks.project_key_format_check import ProjectKeyFormatCheck
import dataikuapi
from python-lib.project_advisor.assessments.config import DSSAssessmentConfig

class TestProjectKeyFormatCheck(unittest.TestCase):
    
    def setUp(self):
        self.client = MagicMock(spec=dataikuapi.dssclient.DSSClient)
        self.config = MagicMock(spec=DSSAssessmentConfig)
        self.project = MagicMock(spec=dataikuapi.dss.project.DSSProject)
    
    def test_valid_project_key(self):
        self.project.project_key = "ABC12"
        check = ProjectKeyFormatCheck(self.client, self.config, self.project, [])
        check.run()
        self.assertTrue(check.check_pass)
    
    def test_invalid_project_key(self):
        self.project.project_key = "ABCDEFG"
        check = ProjectKeyFormatCheck(self.client, self.config, self.project, [])
        check.run()
        self.assertFalse(check.check_pass)

if __name__ == '__main__':
    unittest.main()