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
            highlights.with_warning(f"Objects of type '{obj_type}' displayed growth of {growth:.2f}% per hour.")

    return highlights


def highlight_metric_growth(long_collection_statistics: LongCollectionStatistics) -> Result:
    objects_with_metrics_growth = [(object_type, stats.metrics_growth_rate) for
                                   object_type, stats in
                                   long_collection_statistics.long_object_type_statistics.items()
                                   if stats.metrics_growth_rate > 0]

    highlights = Result()
    if len(objects_with_metrics_growth):
        for obj_type, growth in objects_with_metrics_growth:
            highlights.with_warning(f"Objects of type '{obj_type}' displayed metric growth of {growth:.2f}% per hour.")

    return highlights


def highlight_property_growth(long_collection_statistics: LongCollectionStatistics) -> Result:
    objects_with_property_growth = [(object_type, stats.properties_growth_rate) for
                                    object_type, stats in
                                    long_collection_statistics.long_object_type_statistics.items()
                                    if stats.properties_growth_rate > 0]

    highlights = Result()
    if len(objects_with_property_growth):
        for obj_type, growth in objects_with_property_growth:
            highlights.with_warning(f"Objects of type '{obj_type}' displayed property growth of {growth:.2f}% per hour")

    return highlights


def highlight_property_value_growth(long_collection_statistics: LongCollectionStatistics) -> Result:
    objects_with_property_value_growth = [(object_type, stats.property_values_growth_rate) for
                                          object_type, stats in
                                          long_collection_statistics.long_object_type_statistics.items()
                                          if stats.property_values_growth_rate > 0]

    MAX_NUMBER_OF_PROPERTY_VALUES = min(32, long_collection_statistics.total_number_of_collections)
    threshold = get_growth_rate(1, MAX_NUMBER_OF_PROPERTY_VALUES, long_collection_statistics.long_run_duration)

    highlights = Result()
    if len(objects_with_property_value_growth):
        for obj_type, growth in objects_with_property_value_growth:
            if growth > threshold:
                highlights.with_error(
                    f"Objects of type '{obj_type}' displayed excessive property value growth of {growth:.2f}% per hour.")
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
            highlights.with_warning(f"Objects of type '{obj_type}' displayed relationship growth of {growth:.2f}% per hour.")

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
                highlights.with_warning(f"Objects of type '{obj_type}' displayed event growth of {growth:.2f}% per hour.")

    return highlights
