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
            highlights.with_information("""High Object growth may afect Aria Operations performance overtime.
                                        The main reason for unqanted object growth can be attributed for to the object identifiers not being unique
                                        or the objects name/key not being constant. The two most common scenarios are:
                                        1. An objects identifiers aren't unique which may lead to a collection always collecting the same amount of object
                                        per colleciton, but their overall identifiers not matching with previously collected objects
                                        to resolve this we would look at the objects identifiers and ensure they stay constant overtime

                                        2. A collection returns more and more Objects every time(less common). Ususally this may be an actual bug in the adapter code, maybe a foor loop
                                        naming objects overtime""") #NOTE: scenario two is much more unlikelly with our sdk since collection data is ephimeral to the container
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
            highlights.with_information("""High metric growth may afect Aria Operations avility to display accurate metric mapping overtime. 
                                        A common cause of metric growth is when the metric's key isn't cosntant/unique.
                                        A solution would be to create constatns for each metric key.
                                        """) #Explain how we calculate metric growth so users don't assume that object growth will cause metric growth
    return highlights


def highlight_property_growth(long_collection_statistics: LongCollectionStatistics) -> Result:
    objects_with_property_growth = [(object_type, stats.properties_growth_rate) for
                                    object_type, stats in
                                    long_collection_statistics.long_object_type_statistics.items()
                                    if stats.properties_growth_rate > 0]

    highlights = Result()
    if len(objects_with_property_growth):
        for obj_type, growth in objects_with_property_growth:
            highlights.with_warning("Objects of type '{obj_type}' grew properties at a rate of {growth:.2f}% per hour")
            highlights.with_information("""Porperty growth may reduced performance in Aria Operation and may lead to unstable relationships.
                                        A common cause of property growth is when the property's key isn't cosntant/unique.
                                        A solution would be to create constatns for each property key.""")

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
                highlights.with_information("""Property value growth may cause reduced performance in Aria Operations.
                                            A Commmon cause of property value growth is the use of time stamps or other similarly changing string as values. 
                                            This practice is discourage by Aria Operations as property values should be reserved for small finite sets.
                                            Creating enums for each property value may help aliviate execive property growth. At the same time if there is too many 
                                            possible enumm/values for a property it might indicate that the value should not be considered a property
                                            """)
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
                                        Relationship grwoth may be a sideefect of other types of growth as properties are oftentimes generated based on and objects existence
                                        and a property value. However, there are also cases where property growth is not a sideefect of other types of growth in which case a common cause
                                        is when a relationship between a parent an a child isn't consistent. Aria Ops expects relationships between parent and child to be reported 
                                        every collection time there is a change, so it's important to ensure that relationships changes are reported every time, otherwise Aria Ops will 
                                        assume the relationship no longer exists.
                                        """)

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
                                            Event gwoth is common in Aria Operations, however, execive number of events may be indicative of a bug or unwanted events being reported.
                                            A common scenario of this is when an API returns all events instead of active events. By fitering events and ensuring there is no bungs during
                                            the creation of event may help mitigate this warning 
                                            """)
    return highlights
