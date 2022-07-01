class Result:
    def __init__(self, errors=None, warnings=None):

        if warnings is None:
            warnings = []
        if errors is None:
            errors = []
        self.errors = errors
        self.warnings = warnings

    def __iadd__(self, other):
        self.errors = self.errors + other.errors
        self.warnings = self.warnings + other.warnings
        return self

    def with_error(self, error):
        self.errors.append(error)

    def with_warning(self, warning):
        self.warnings.append(warning)
