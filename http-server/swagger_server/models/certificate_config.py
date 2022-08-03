# coding: utf-8

#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server.models.certificate import Certificate  # noqa: F401,E501
from swagger_server import util


class CertificateConfig(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """
    def __init__(self, certificates: List[Certificate]=None):  # noqa: E501
        """CertificateConfig - a model defined in Swagger

        :param certificates: The certificates of this CertificateConfig.  # noqa: E501
        :type certificates: List[Certificate]
        """
        self.swagger_types = {
            'certificates': List[Certificate]
        }

        self.attribute_map = {
            'certificates': 'certificates'
        }
        self._certificates = certificates

    @classmethod
    def from_dict(cls, dikt) -> 'CertificateConfig':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The CertificateConfig of this CertificateConfig.  # noqa: E501
        :rtype: CertificateConfig
        """
        return util.deserialize_model(dikt, cls)

    @property
    def certificates(self) -> List[Certificate]:
        """Gets the certificates of this CertificateConfig.


        :return: The certificates of this CertificateConfig.
        :rtype: List[Certificate]
        """
        return self._certificates

    @certificates.setter
    def certificates(self, certificates: List[Certificate]):
        """Sets the certificates of this CertificateConfig.


        :param certificates: The certificates of this CertificateConfig.
        :type certificates: List[Certificate]
        """

        self._certificates = certificates
