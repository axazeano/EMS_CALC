import time

__author__ = 'kubantsev'

import urllib2
import threading
import json
import httplib
import logging

logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                        level=logging.DEBUG)
# TODO: set correct logging config


class EMS_API():
    def __init__(self):
        self.base_api_url = 'http://emspost.ru/api/rest/'
        self.methods = {
            'echo': 'ems.test.echo',
            'get_max_weight': 'ems.get.max.weight',
            'get.locations': 'ems.get.locations',
            'calculate': 'ems.calculate'
        }

    def make_url_for(self, method, **kwargs):
        url = self.base_api_url + '?method=' + self.methods[method]
        for key, value in kwargs.iteritems():
            url += '&' + key + '=' + value
        # from is python keyword
        url = url.replace('from_location', 'from')
        return url

    def heartbeat(self):
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
        response = APIUtils.safe_connection(self.make_url_for('get_max_weight'))
        parsed_json_object = APIUtils.safe_json_parse(response)
        if parsed_json_object:
            return parsed_json_object['rsp']['max_weight']
        else:
            logging.error('Method ems.get.max.weight: error. Trying again...')
            time.sleep(5)
            return self.get_max_weight()

    def get_locations(self, type, plain='false'):
        response = APIUtils.safe_connection(self.make_url_for('get.locations',
                                                              type=type,
                                                              plain=plain))
        parsed_json_object = APIUtils.safe_json_parse(response)
        if parsed_json_object:
            return parsed_json_object['rsp']['locations']
        else:
            return None

    def calculate(self, from_location, to_location, weight, type):
        response = APIUtils.safe_connection(self.make_url_for('calculate',
                                                     from_location=from_location,
                                                     to=to_location,
                                                     weight=weight,
                                                     type=type))
        return APIUtils.safe_json_parse(response)


class APIUtils:
    """
    Class contains some functions for work with REST API.
    """

    @staticmethod
    def safe_connection(url):
        """
        Try connect to url and read data. If error happened, check witch exception was raised.
        :param url: url for connection
        :return: Return data from URL, in case when all works fine, else return None
        """
        try:
            response = urllib2.urlopen(url)
        except urllib2.HTTPError, e:
            logging.error('HTTPError = ' + str(e.code))
        except urllib2.URLError:
            logging.error('URLError')
        except httplib.HTTPException:
            logging.error('URLError')
        else:
            logging.debug(url + ' has be successfully opened')
            return response.read()
        return None

    @staticmethod
    def safe_json_parse(json_string):
        """
        Try to parse incoming json object
        :param json_string: incoming string with json object
        :return: if json_string jas been parsed without errors return parsed object, else return None
        """
        try:
            parsed_json = json.loads(json_string)
        except TypeError, e:
            logging.error('Parse error')
            return None
        else:
            logging.debug('JSON parsed successfully')
            return parsed_json
