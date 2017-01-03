import unittest
import json
from Cache import NotCache


class testCache(unittest.TestCase):
    def setUp(self):
        self.cache = NotCache()

    def test_set_values(self):
        input = {'module': 'NFM', 'id': 222, 'nfm1': 1, 'nfm2': 2, 'nfm3': 3 }

        output = json.loads(self.cache.set_values(json.dumps(input)))
        assert output, dict
        # test if output dict is a superset of input dict
        self.assertDictContainsSubset(input, output, "output dict not of the correct format")

    def test_get_values(self):
        keylist = ['nfm1','nfm2', 'nfm3']
        input = {'module': 'NFM', 'id': 222, 'keylist': keylist }

        output = self.cache.get_values(json.dumps(input))
        assert output, list

        listkeys = []
        for tupl in output:
            listkeys.append(tupl[0])

        for key in keylist:
            self.assertIn(key,listkeys, "input key not in output list")




SetValuesTestCase = testCache('test_set_values')
GetValuesTestCase = testCache('test_get_values')


