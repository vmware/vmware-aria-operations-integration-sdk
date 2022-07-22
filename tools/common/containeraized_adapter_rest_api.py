from common.timer import timed
import requests


@timed
def get(url, headers):
    request = requests.models.Request(method="GET",
                                      url=url,
                                      headers=headers)
    response = requests.get(url=url, headers=headers)
    return request, response


@timed
def post(url, json, headers):
    request = requests.models.Request(method="POST", url=url,
                                      json=json,
                                      headers=headers)
    response = requests.post(url=url, json=json, headers=headers)
    return request, response
