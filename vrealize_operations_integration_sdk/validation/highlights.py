from vrealize_operations_integration_sdk.collection_statistics import LongCollectionStatistics
from vrealize_operations_integration_sdk.stats import get_growth_rate
from vrealize_operations_integration_sdk.validation.result import Result


def highlight_object_growth(long_collection_statistics: LongCollectionStatistics) -> Result:
    objects_with_growth = [(object_type, stats.objects_growth_rate) for
                           object_type, stats in
                           long_collection_statistics.long_object_type_statistics.items()
                           if stats.objects_growth_rate > 0]

    highlights = Result()
    if len(objects_with_growth):
        for obj_type, growth in objects_with_growth:
            highlights.with_warning(f"Objects of type '{obj_type}' grew at a rate of {growth:.2f}% per hour.")
            highlights.with_information("""
High Object growth may affect Aria Operations' performance over time.
- Check that object identifiers are not changing. 
- Ensure that there are no short-lived objects (eg. sessions).""") 
    return highlights


def highlight_metric_growth(long_collection_statistics: LongCollectionStatistics) -> Result:
    objects_with_metrics_growth = [(object_type, stats.metrics_growth_rate) for
                                   object_type, stats in
                                   long_collection_statistics.long_object_type_statistics.items()
                                   if stats.metrics_growth_rate > 0]

    highlights = Result()
    if len(objects_with_metrics_growth):
        for obj_type, growth in objects_with_metrics_growth:
            highlights.with_warning(f"Metrics on objects of type '{obj_type}' grew at a rate of {growth:.2f}% per hour.")
            highlights.with_information("""
High metric growth may affect Aria Operations' performance over time.  
Metric growth is caused by new or changing metric keys. One way to ensure metric keys are the same is to use 
constants to describe their keys; Aria Operations works best with a constant set of metrics per object type.""")
    return highlights


def highlight_property_growth(long_collection_statistics: LongCollectionStatistics) -> Result:
    objects_with_property_growth = [(object_type, stats.properties_growth_rate) for
                                    object_type, stats in
                                    long_collection_statistics.long_object_type_statistics.items()
                                    if stats.properties_growth_rate > 0]

    highlights = Result()
    if len(objects_with_property_growth):
        for obj_type, growth in objects_with_property_growth:
            highlights.with_warning(f"Properties on objects of type '{obj_type}' grew at a rate of {growth:.2f}% per hour.")
            highlights.with_information("""
High property growth may affect Aria Operations' performance over time.  
Property growth is caused by new or changing property keys. One way to ensure property keys are the same is to use 
constants to describe their keys; Aria Operations works best with a constant set of properties per object type.""")

    return highlights


def highlight_property_value_growth(long_collection_statistics: LongCollectionStatistics) -> Result:
    objects_with_property_value_growth = [(object_type, stats.property_values_growth_rate) for
                                          object_type, stats in
                                          long_collection_statistics.long_object_type_statistics.items()
                                          if stats.property_values_growth_rate > 0]

    MAX_NUMBER_OF_PROPERTY_VALUES = min(32, long_collection_statistics.total_number_of_collections)
    threshold = get_growth_rate(1, MAX_NUMBER_OF_PROPERTY_VALUES, long_collection_statistics.long_run_duration / 3600)

    # NOTE: We combine all property values into a single set, which looses the avility to get the property key 
    highlights = Result()
    if len(objects_with_property_value_growth):
        for obj_type, growth in objects_with_property_value_growth:
            if growth >= threshold:
                highlights.with_error(
                    f"Property values on objects of '{obj_type}' grew at a rate of {growth:.2f}% per hour.")
            else:
                 highlights.with_warning(f"Property values on objects of '{obj_type}' grew at a rate of {growth:.2f}% per hour.")

            highlights.with_information("""
High property value growth may affect Aria Operations' performance over time. Property value growth is caused by 
setting a property values to unique value frequently. Property values should be finite and change infrequently. Creating enums for
each property value may help establish a finite set of possible values. If the amount of possible enums values is too large
or the value changes frequently, consider a metric with a numeric value. For example, using a human-readable (string) time 
stamp as a property to record the last backup date, should be replaced. A possible alternative could be a metric that counts
days since last backup.""")

    return highlights


def highlight_event_growth(long_collection_statistics: LongCollectionStatistics) -> Result:
    objects_with_event_growth = [(object_type, stats.events_growth_rate) for
                                 object_type, stats in
                                 long_collection_statistics.long_object_type_statistics.items()
                                 if stats.events_growth_rate > 0]

    threshold = get_growth_rate(0, (10000 * long_collection_statistics.long_run_duration / 3600),
                                long_collection_statistics.long_run_duration)
    highlights = Result()
    if len(objects_with_event_growth):
        for obj_type, growth in objects_with_event_growth:
            if growth > threshold:
                highlights.with_warning(f"Events on objects of type '{obj_type}' grew at a rate of {growth:.2f}% per hour.")
                highlights.with_information("""
An excessive number of events may indicate a bug or over-reporting.
Overreporting can occur when an API reports all events instead of active events, and the Adapter creates more
and more events each time. Filtering events based on status or a time window may fix this issue.""")
    return highlights

# TODO: highlight relationships
