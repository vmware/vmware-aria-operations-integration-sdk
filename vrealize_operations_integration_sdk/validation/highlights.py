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
Most often, changing object identifiers cause object growth over time.
Ensure object Identifiers are unique and constant.""") #NOTE: scenario two is much more unlikelly with our sdk since collection data is ephimeral to the container
    return highlights


def highlight_metric_growth(long_collection_statistics: LongCollectionStatistics) -> Result:
    objects_with_metrics_growth = [(object_type, stats.metrics_growth_rate) for
                                   object_type, stats in
                                   long_collection_statistics.long_object_type_statistics.items()
                                   if stats.metrics_growth_rate > 0]

    highlights = Result()
    if len(objects_with_metrics_growth):
        for obj_type, growth in objects_with_metrics_growth:
            highlights.with_warning(f"Objects of type '{obj_type}' grew metrics at a rate of {growth:.2f}% per hour.")
            highlights.with_information("""
High metric growth may affect Aria Operations' ability to display accurate metric statistics.
Most often, changing metric keys cause metric growth. To ensure metric keys are the same, use constants to describe their keys.""")
    return highlights


def highlight_property_growth(long_collection_statistics: LongCollectionStatistics) -> Result:
    objects_with_property_growth = [(object_type, stats.properties_growth_rate) for
                                    object_type, stats in
                                    long_collection_statistics.long_object_type_statistics.items()
                                    if stats.properties_growth_rate > 0]

    highlights = Result()
    if len(objects_with_property_growth):
        for obj_type, growth in objects_with_property_growth:
            highlights.with_warning(f"Objects of type '{obj_type}' grew properties at a rate of {growth:.2f}% per hour")
            highlights.with_information("""
Property growth may lead to unstable object relationships. Most often, changing property keys cause property growth.
Avoid mapping API keys to property keys and use constants to describe property keys.""")

    return highlights


def highlight_property_value_growth(long_collection_statistics: LongCollectionStatistics) -> Result:
    objects_with_property_value_growth = [(object_type, stats.property_values_growth_rate) for
                                          object_type, stats in
                                          long_collection_statistics.long_object_type_statistics.items()
                                          if stats.property_values_growth_rate > 0]

    MAX_NUMBER_OF_PROPERTY_VALUES = min(32, long_collection_statistics.total_number_of_collections)
    threshold = get_growth_rate(1, MAX_NUMBER_OF_PROPERTY_VALUES, long_collection_statistics.long_run_duration / 3600)

    highlights = Result()
    if len(objects_with_property_value_growth):
        for obj_type, growth in objects_with_property_value_growth:
            if growth >= threshold:
                highlights.with_error(
                    f"Objects of type '{obj_type}' displayed excessive property value growth of {growth:.2f}% per hour.")
                highlights.with_information("""
Property value growth may cause reduced Aria Operations performance. Most often, property value growth is driven by
constantly changing property values. Property values should be finite and change infrequently. Creating enums for
each property value may help establish a finite set of possible values. If the amount of possible enums is too large
or the value changes frequently, consider a metric with a numeric value.""")
            else:
                highlights.with_warning(f"Objects of type '{obj_type}' displayed property value growth of {growth:.2f}% per hour.")

    return highlights


def highlight_relationship_growth(long_collection_statistics: LongCollectionStatistics) -> Result:
    objects_with_relationships_growth = [(object_type, stats.relationships_growth_rate) for
                                         object_type, stats in
                                         long_collection_statistics.long_object_type_statistics.items()
                                         if stats.relationships_growth_rate > 0]

    highlights = Result()
    if len(objects_with_relationships_growth):
        for obj_type, growth in objects_with_relationships_growth:
            highlights.with_warning(f"Objects of type '{obj_type}' grew at a rate of {growth:.2f}% per hour.")
            highlights.with_information("""
Relationship growth may be a side effect of other growth types. However, there are cases where relationship growth is not
a side effect of other growths. Most often, poor relationship reporting is a cause of relationship growth. An adapter should
report changed relationships only. Reporting the same relationships every cycle has the same effect as reporting the relationship
once, and not reporting anything else. Aria Operations filters out unnecessary changes before writing to the database.""")

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
                highlights.with_warning(f"Objects of type '{obj_type}' grew at a rate of {growth:.2f}% per hour.")
                highlights.with_information("""
Event growth is typical in Aria Operations; however, an exesive number of events may indicate a bug or over-reporting.
Most often, overreporting occurs when an API reports all events instead of active events, and the Adapter creates more
and more events each time. Filtering events based on status can fix this issue.""")
    return highlights
