class ToolKitError(Exception):
    pass


class ConfigError(ToolKitError):
    pass


class ScraperError(ToolKitError):
    pass


class ExtractorError(ToolKitError):
    pass


class PipelineError(ToolKitError):
    pass


class ValidationError(ToolKitError):
    pass