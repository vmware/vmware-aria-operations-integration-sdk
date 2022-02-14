# swagger_client.DefaultApi

All URIs are relative to *http://localhost:8000*

Method | HTTP request | Description
------------- | ------------- | -------------
[**collect**](DefaultApi.md#collect) | **POST** /collect | Data Collection
[**get_endpoint_urls**](DefaultApi.md#get_endpoint_urls) | **POST** /endpointURLs | Retrieve endpoint URLs
[**test**](DefaultApi.md#test) | **POST** /test | Connection Test
[**version**](DefaultApi.md#version) | **GET** /version | Adapter Version

# **collect**
> CollectResult collect(body=body)

Data Collection

Do data collection

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.DefaultApi()
body = swagger_client.AdapterConfig() # AdapterConfig |  (optional)

try:
    # Data Collection
    api_response = api_instance.collect(body=body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DefaultApi->collect: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**AdapterConfig**](AdapterConfig.md)|  | [optional] 

### Return type

[**CollectResult**](CollectResult.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_endpoint_urls**
> list[str] get_endpoint_urls(body=body)

Retrieve endpoint URLs

This should return a list of properly formed endpoint URL(s) (https://ip address) this adapter instance is expected to communicate with. List of URLs will be used for taking advantage of the vRealize Operations Manager certificate trust system. If the list is empty this means adapter will handle certificates manully.

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.DefaultApi()
body = swagger_client.AdapterConfig() # AdapterConfig |  (optional)

try:
    # Retrieve endpoint URLs
    api_response = api_instance.get_endpoint_urls(body=body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DefaultApi->get_endpoint_urls: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**AdapterConfig**](AdapterConfig.md)|  | [optional] 

### Return type

**list[str]**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **test**
> TestResult test(body=body)

Connection Test

Trigger a connection test

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.DefaultApi()
body = swagger_client.AdapterConfig() # AdapterConfig |  (optional)

try:
    # Connection Test
    api_response = api_instance.test(body=body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DefaultApi->test: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**AdapterConfig**](AdapterConfig.md)|  | [optional] 

### Return type

[**TestResult**](TestResult.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **version**
> str version()

Adapter Version

Get Adapter Version

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.DefaultApi()

try:
    # Adapter Version
    api_response = api_instance.version()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DefaultApi->version: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

**str**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

