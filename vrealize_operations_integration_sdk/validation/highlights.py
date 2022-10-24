from collection_statistics import LongCollectionStatistics
from validation.result import Result


def highlight_object_growth(long_collection_statistics: LongCollectionStatistics) -> Result:
    objects_with_growth = [(object_type, stats.objects_growth_rate) for
                           object_type, stats in
                           long_collection_statistics.long_object_type_statistics.items()
                           if stats.objects_growth_rate > 0]

    # get overall object growth rate in order to asses scenario # 2
    # find first successful collection and count number of objects
    unique_object_per_collection = [0] * long_collection_statistics.total_number_of_collections
    unique_object_per_collection[0] = len(long_collection_statistics.collection_bundles[0]
                                          .get_collection_statistics().obj_type_statistics)
    unique_object_per_collection[-1] = len(long_collection_statistics.long_object_type_statistics)

    highlights = Result()
    if len(objects_with_growth):
        for obj_type, growth in objects_with_growth:
            new_result = Result()
            new_result.with_warning(f"Object of type {obj_type} displayed growth of {growth:.2f}")
            highlights += new_result

    return highlights
