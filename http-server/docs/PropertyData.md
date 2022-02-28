# PropertyData

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**key** | **str** | Key represents a hierarchical structure for an individual metric. The formation of the metric key is an important part of designing a data feed. Well formed metric keys will lead to better usability, performance and visualization of analytics results, such as root cause analysis.  The base concepts are as follows:&lt;br&gt; A metric key can consist of any number of hierarchical groups. Each hierarchical group can contain instances. The last item in the hierarchy is assumed to be the name of the metric. The hierarchy without instance names represents an attribute that can be collected. If there are no instances, then a metric key and an attribute are one and the same. | 
**string_value** | **str** | Current string value | [optional] 
**number_value** | **float** | Current double value. | [optional] 
**timestamp** | **int** | Timestamp of the data. | [optional] [default to -1]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)

