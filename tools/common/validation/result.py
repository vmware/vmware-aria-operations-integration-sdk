class Result:
    def __init__(self, errors=list, warnings=list):
        self.errors = errors
        self.warnings = warnings

    def __iadd__(self, other):
        self.errors += other.errors
        self.warnings += other.warnins

    def with_error(self, error):
        self.errors.append(error)

    def with_warning(self, warning):
        self.errors.append(warning)
