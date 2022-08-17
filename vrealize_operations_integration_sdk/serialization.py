class CollectionBundle:
    def __init__(self, container_stats, duration, request, response, collection_stats=None, json=None):
        self.container_stats = container_stats
        self.duration = duration
        self.request = request
        self.response = response
        self.collection_stats = collection_stats
        self.json = json

    def serialize(self):
        pass

    def to_html(self):
        pass

    def is_failed(self) -> bool:
        pass
