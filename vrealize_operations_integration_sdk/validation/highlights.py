from collection_statistics import LongCollectionStatistics
from validation.result import Result


def highlight_object_growth(long_collection_statistics: LongCollectionStatistics) -> Result:
    objects_with_growth = [(object_type, stats.objects_growth_rate) for
                           object_type, stats in
                           long_collection_statistics.long_object_type_statistics.items()
                           if stats.objects_growth_rate > 0]

    highlights = Result()
    if len(objects_with_growth):
        for obj_type, growth in objects_with_growth:
            highlights.with_warning(f"Object of type {obj_type} displayed growth of {growth:.2f}")

    return highlights


def highlight_metric_growth(long_collection_statistics: LongCollectionStatistics) -> Result:
    objects_with_metrics_growth = [(object_type, stats.metrics_growth_rate) for
                                   object_type, stats in
                                   long_collection_statistics.long_object_type_statistics.items()
                                   if stats.metrics_growth_rate > 0]

    highlights = Result()
    if len(objects_with_metrics_growth):
        for obj_type, growth in objects_with_metrics_growth:
            highlights.with_warning(f"Object of type {obj_type} displayed metric growth of {growth:.2f}")

    return highlights


def highlight_property_growth(long_collection_statistics: LongCollectionStatistics) -> Result:
    objects_with_property_growth = [(object_type, stats.properties_growth_rate) for
                                    object_type, stats in
                                    long_collection_statistics.long_object_type_statistics.items()
                                    if stats.properties_growth_rate > 0]

    highlights = Result()
    if len(objects_with_property_growth):
        for obj_type, growth in objects_with_property_growth:
            highlights.with_warning(f"Object of type {obj_type} displayed property growth of {growth:.2f}")

    return highlights


def highlight_property_value_growth(long_collection_statistics: LongCollectionStatistics) -> Result:
    objects_with_property_value_growth = [(object_type, stats.property_values_growth_rate) for
                                          object_type, stats in
                                          long_collection_statistics.long_object_type_statistics.items()
                                          if stats.property_values_growth_rate > 0]

    # TODO define threshold
    highlights = Result()
    if len(objects_with_property_value_growth):
        for obj_type, growth in objects_with_property_value_growth:
            highlights.with_warning(f"Object of type {obj_type} displayed property value growth of {growth:.2f}")

    return highlights


def highlight_relationship_growth(long_collection_statistics: LongCollectionStatistics) -> Result:
    objects_with_relationships_growth = [(object_type, stats.relationships_growth_rate) for
                                         object_type, stats in
                                         long_collection_statistics.long_object_type_statistics.items()
                                         if stats.relationships_growth_rate > 0]

    highlights = Result()
    if len(objects_with_relationships_growth):
        for obj_type, growth in objects_with_relationships_growth:
            highlights.with_warning(f"Object of type {obj_type} displayed relationship growth of {growth:.2f}")

    return highlights


def highlight_event_growth(long_collection_statistics: LongCollectionStatistics) -> Result:
    objects_with_event_growth = [(object_type, stats.events_growth_rate) for
                                 object_type, stats in
                                 long_collection_statistics.long_object_type_statistics.items()
                                 if stats.events_growth_rate > 0]

    # calculate threshold 1000 + event growth
    highlights = Result()
    if len(objects_with_event_growth):
        for obj_type, growth in objects_with_event_growth:
            highlights.with_warning(f"Object of type {obj_type} displayed event growth of {growth:.2f}")

    return highlights
