# Identifier

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**key** | **str** | Key for the object identifier. For a object kind, identifier keys are unique. In describe.xml file, the attribute \&quot;key\&quot; corresponds to this field. This is a case-insensitive field and can not be empty. | 
**value** | **str** | Value of the object identifier. This is a case-insensitive field | [optional] 
**is_part_of_uniqueness** | **bool** | Flag to indicate whether the identifier should be considered for object&#x27;s uniqueness. If a object has multiple identifiers that are part of uniqueness, there can be only one combination of values of those identifiers in vRealize Operations. | [optional] [default to False]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)

