import json
import os
import requests
import requests.packages.urllib3

global pprint_j

requests.packages.urllib3.disable_warnings()


# Helper to pretty print json
def pprint_j(i):
    print(json.dumps(i, indent=4, sort_keys=True))


class dbclient:
    """
    Rest API Wrapper for Databricks APIs
    """
    # set of http error codes to throw an exception if hit. Handles client and auth errors
    http_error_codes = (401, 403)

    def __init__(self, configs):
        self._token = {'Authorization': 'Bearer {0}'.format(configs['token'])}
        self._url = configs['url'].rstrip("/")
        self._export_dir = configs['export_dir']
        self._is_aws = configs['is_aws']
        self._skip_failed = configs['skip_failed']
        self._is_verbose = configs['verbose']
        self._verify_ssl = configs['verify_ssl']
        if self._verify_ssl:
            # set these env variables if skip SSL verification is enabled
            os.environ['REQUESTS_CA_BUNDLE'] = ""
            os.environ['CURL_CA_BUNDLE'] = ""
        os.makedirs(self._export_dir, exist_ok=True)

    def is_aws(self):
        return self._is_aws

    def is_verbose(self):
        return self._is_verbose

    def is_skip_failed(self):
        return self._skip_failed

    def test_connection(self):
        # verify the proper url settings to configure this client
        if self._url[-4:] != '.com':
            print("Hostname should end in '.com'")
            return -1
        results = requests.get(self._url + '/api/2.0/clusters/spark-versions', headers=self._token,
                               verify=self._verify_ssl)
        http_status_code = results.status_code
        if http_status_code != 200:
            print("Error. Either the credentials have expired or the credentials don't have proper permissions.")
            print("If you have a ~/.netrc file, check those credentials. Those take precedence over passed input.")
            print(results.text)
            return -1
        return 0

    def get(self, endpoint, json_params=None, version='2.0', print_json=False):
        if version:
            ver = version
        full_endpoint = self._url + '/api/{0}'.format(ver) + endpoint
        if self.is_verbose():
            print("Get: {0}".format(full_endpoint))
        if json_params:
            raw_results = requests.get(full_endpoint, headers=self._token, params=json_params, verify=self._verify_ssl)
            http_status_code = raw_results.status_code
            if http_status_code in dbclient.http_error_codes:
                raise Exception("Error: GET request failed with code {}\n{}".format(http_status_code, raw_results.text))
            results = raw_results.json()
        else:
            raw_results = requests.get(full_endpoint, headers=self._token, verify=self._verify_ssl)
            http_status_code = raw_results.status_code
            if http_status_code in dbclient.http_error_codes:
                raise Exception("Error: GET request failed with code {}\n{}".format(http_status_code, raw_results.text))
            results = raw_results.json()
        if print_json:
            print(json.dumps(results, indent=4, sort_keys=True))
        if type(results) == list:
            results = {'elements': results}
        results['http_status_code'] = raw_results.status_code
        return results

    def http_req(self, http_type, endpoint, json_params, version='2.0', print_json=False):
        if version:
            ver = version
        full_endpoint = self._url + '/api/{0}'.format(ver) + endpoint
        if self.is_verbose():
            print("{0}: {1}".format(http_type, full_endpoint))
        if json_params:
            if http_type == 'post':
                raw_results = requests.post(full_endpoint, headers=self._token,
                                            json=json_params, verify=self._verify_ssl)
            if http_type == 'put':
                raw_results = requests.put(full_endpoint, headers=self._token,
                                           json=json_params, verify=self._verify_ssl)
            if http_type == 'patch':
                raw_results = requests.patch(full_endpoint, headers=self._token,
                                             json=json_params, verify=self._verify_ssl)
            http_status_code = raw_results.status_code
            if http_status_code in dbclient.http_error_codes:
                raise Exception("Error: {0} request failed with code {1}\n{2}".format(http_type,
                                                                                      http_status_code,
                                                                                      raw_results.text))
            results = raw_results.json()
        else:
            print("Must have a payload in json_args param.")
            return {}
        if print_json:
            print(json.dumps(results, indent=4, sort_keys=True))
        # if results are empty, let's return the return status
        if results:
            results['http_status_code'] = raw_results.status_code
            return results
        else:
            return {'http_status_code': raw_results.status_code}

    def post(self, endpoint, json_params, version='2.0', print_json=False):
        return self.http_req('post', endpoint, json_params, version, print_json)

    def put(self, endpoint, json_params, version='2.0', print_json=False):
        return self.http_req('put', endpoint, json_params, version, print_json)

    def patch(self, endpoint, json_params, version='2.0', print_json=False):
        return self.http_req('patch', endpoint, json_params, version, print_json)

    @staticmethod
    def my_map(F, items):
        to_return = []
        for elem in items:
            to_return.append(F(elem))
        return to_return
