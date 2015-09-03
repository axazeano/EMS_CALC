import time

__author__ = 'kubantsev'

import http
from urllib.error import HTTPError
from urllib.request import urlopen
from concurrent import futures
import urllib
import json
import logging

logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.DEBUG)


# TODO: set correct logging config


class EMS_API():
    """
    Realization of EMS customers API
    Description of API: http://www.emspost.ru/ru/corp_clients/dogovor_docements/api/

    API Methods:
        ems.test.echo - method for check available of API

        ems.get.locations - method for get locations.
        Locations are used for define start and finish points of delivery

        ems.get.max.weight - method for get max weight of package

        ems.calculate - method for calculate costs of delivery and duration of delivery (for local delivery)
    """

    def __init__(self):
        self.executor = futures.ThreadPoolExecutor(max_workers=5)
        # Root url for API
        self.base_api_url = 'http://emspost.ru/api/rest/'
        # Methods, that are provided by API
        self.methods = {
            'echo': 'ems.test.echo',
            'get_max_weight': 'ems.get.max.weight',
            'get.locations': 'ems.get.locations',
            'calculate': 'ems.calculate'
        }

    def make_url_for(self, method, **kwargs):
        """
        Produce urls for API calls
        :param method: API method, which will be called
        :param kwargs: Dict where keys are names of params, and values are values of params
        :return: Complete url
        """
        url = self.base_api_url + '?method=' + self.methods[method]
        for key, value in kwargs.items():
            if value is None:
                pass
            else:
                # add to url string '&key=value'
                url += '&{}={}'.format(key, value)
        # from is python keyword
        url = url.replace('from_location', 'from')
        return url

    def heartbeat(self):
        """
        Realization of API Heartbeat. Make request to method ems.test.echo
        and check response
        :return: If API is available, return True, in other cases return False
        """
        response = APIUtils.safe_connection(self.make_url_for('echo'))
        if response:
            parsed_response = APIUtils.safe_json_parse(response)
            if parsed_response['rsp']['msg'] == 'successeful':
                logging.info('HeartBeat: EMS API is available')
                return True
            else:
                logging.info('HeartBeat: EMS API is unavailable')
                return False
        else:
            logging.error('HeartBeat: Empty heartbeat msg')
            return False

    def get_max_weight(self):
        """
        Realization of method ems.get.max.weight
        :return: max_weight from response or None
        """
        response = APIUtils.safe_connection(self.make_url_for('get_max_weight'))
        parsed_json_object = APIUtils.safe_json_parse(response)
        if parsed_json_object:
            return float(parsed_json_object['rsp']['max_weight'])
        else:
            return None

    def get_locations(self, type):
        """
        Realization of method ems.get.locations
        :param type: type of locations. May be equals 'russia', 'cities', 'regions', 'countries'
        :return: locations value from response or None
        """
        response = APIUtils.safe_connection(self.make_url_for('get.locations', type=type))
        # response = APIUtils.safe_connection_done()
        parsed_json_object = APIUtils.safe_json_parse(response)
        if parsed_json_object:
            return parsed_json_object['rsp']['locations']
        else:
            return None

    def calculate(self, to_location, weight, from_location=None, type=None):
        """
        Implementation of method ems.calculate
        :param to_location: is Required for both delivery types
        :param weight: is Required for both delivery types
        :param from_location: is Required for local delivery, by default is None
        :param type: is Required for international delivery
        :return: Return dict with price, min_days, max_days for local delivery,
        dict with price for international delivery
        """
        response = APIUtils.safe_connection(self.make_url_for('calculate',
                                                                from_location=from_location,
                                                                to=to_location,
                                                                type=type,
                                                                weight=weight))

        parsed_json_object = APIUtils.safe_json_parse(response)
        # Check that parsed_json_object isn't empty
        if parsed_json_object:
            # Case for local delivery
            if from_location is None:
                return {'price': parsed_json_object['rsp']['price']}
            # Case for international delivery
            else:
                return {'price': parsed_json_object['rsp']['price'],
                        'min_days': parsed_json_object['rsp']['term']['min'],
                        'max_days': parsed_json_object['rsp']['term']['max']}
        # If parsed_json_object is empty method returns None
        else:
            return None


class APIUtils:
    """
    Class contains some functions for work with REST API.
    """

    @staticmethod
    def safe_connection(url):
            """
            Method opens url in try catch block.
            :return: If url has been opened without exceptions return decoded in utf-8  data from response
            """
            try:
                response = urlopen(url)
            except HTTPError as e:
                logging.error('HTTPError = ' + str(e.code))
            except urllib.error.URLError:
                logging.error('URLError')
            except http.client.HTTPException:
                logging.error('URLError')
            else:
                logging.debug(url + ' has been successfully opened')
                return response.read().decode("utf-8")
            return None

    @staticmethod
    def safe_json_parse(json_string):
        """
        Method, which  parses json object in try catch block and add error in log,
        when exceptions are raised
        :param json_string: string, witch will be parse
        :return: In case when parse done without exceptions return dict with parsed json object.
        In other cases returns None.
        """
        try:
            parsed_json = json.loads(json_string)
        except ValueError as e:
            logging.error('Parse error')
            return None
        except TypeError as e:
            logging.error('Empty JSON object')
            return None
        else:
            if parsed_json['rsp']['stat'] == u'ok':
                logging.debug('JSON parsed successfully')
                return parsed_json
            else:
                logging.error('Error Message: {} ; Code: {}'.format(parsed_json['rsp']['err']['msg'],
                                                                    parsed_json['rsp']['err']['code']))
                return None
