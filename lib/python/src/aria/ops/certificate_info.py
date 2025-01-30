#  © 2025 Broadcom. All Rights Reserved.
#  The term “Broadcom” refers to Broadcom Inc. and/or its subsidiaries.
#  SPDX-License-Identifier: Apache-2.0
from cryptography import x509


class CertificateInfo(object):
    """Class representing an x509 certificate for verifying an SSL connection."""

    def __init__(self, certificate: dict) -> None:
        self.certificate = certificate

    def get_certificate_string(self) -> str:
        """
        Gets a string representation of the certificate.
        Returns:
            str: String representation of the certificate.
        """
        return str(self.certificate.get("cert_pem_string"))

    def get_certificate_object(self) -> x509.Certificate:
        """
        Gets the certificate as an x509.Certificate object.
        Returns:
            x509.Certificate: the certificate.
        """
        return x509.load_pem_x509_certificate(self.get_certificate_string().encode())

    def is_expired_certificate_accepted(self) -> bool:
        """
        Returns:
            bool: True if the certificate can be used if it is expired.
        """
        return bool(self.certificate.get("is_expired_certificate_accepted"))

    def is_invalid_hostname_accepted(self) -> bool:
        """
        Returns:
            bool: True if the certificate can be used if the hostnames do not match.
        """
        return bool(self.certificate.get("is_invalid_hostname_accepted"))
