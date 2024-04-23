import json
from flask import make_response
from classes.http_codes import http_codes


class Response():
    def __init__(self, cd: int, rs=None, d=None, msg=None):
        try:
            # parse the code to a proper type
            self.status_code = str(cd)

            if msg != None:
                self.status_message = msg
            else:
                # propely format the response message
                self.status_message = ' '.join(
                    http_codes[cd][0].capitalize().split('_'))

            if rs != None:
                self.reason = rs

            if d != None:
                self.data = d

        except KeyError as error:
            print('Invalid status code')

    def to_json(self):
        response = make_response(json.dumps(
            self.__dict__), int(self.status_code))
        response.headers['Content-Type'] = 'application/json'
        return response
