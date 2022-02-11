# Certificate

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cert_pem_string** | **str** |  | 
**is_invalid_hostname_accepted** | **bool** | In case if the hostname verification fails and isInvalidHostnameAccepted is true  Adapter should do the verification by comparing the certificates from the endpoints with the certificates received from the Collector.  For example the comparison can be done by thumbprint. | [optional] [default to False]
**is_expired_certificate_accepted** | **bool** | In case if the connection fails because of certificate expiration and isExpiredCertificateAccepted is true then the Adapter should ignore that failure and continue the connection. | [optional] [default to False]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)

