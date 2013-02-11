import unittest

from licensing.data import licence_application

class LicenceApplicationTest(unittest.TestCase):

    def setUp(self):
        self.visit = licence_application.LicenceApplication.from_google_row('www.foo.com/apply-for-a-licence/licence-name/authority/interaction-X','republic of test', '7', '2012-01-01', '2012-01-31')

    def test_licence_extraction(self):
        self.assertEqual(self.visit.licence, 'licence-name')

    def test_authority_extraction(self):
        self.assertEqual(self.visit.authority, 'authority')

    def test_interaction_extraction(self):
        self.assertEqual(self.visit.interaction, 'interaction-X')

    def test_location(self):
        self.assertEqual(self.visit.location, 'republic of test')

    def test_equality(self):
        another_application = licence_application.LicenceApplication.from_google_row('www.foo.com/apply-for-a-licence/licence-name/authority/interaction-X','republic of test', '7', '2012-01-01', '2012-01-31')
        self.assertEqual(self.visit, another_application)


class LicenceApplicationBatchCreation(unittest.TestCase):

    def setUp(self):
        # url, country, visits
        self.stub_google_results_1 = [['/foo/bar/zap/boom','testopia','1'],['/foo/bar/zap/boom','test republic','2']]
        self.stub_google_results_2 = [['/foo/bar/zap/boom','testopia','1'],['not valid','test republic','1']]

    def test_batch_creation_of_licence_applications(self):
        licence_applications = licence_application.from_google_data(self.stub_google_results_1, '2012-01-01', '2012-01-31')
        #should create an application for each row
        self.assertEqual(len(list(licence_applications)),2)