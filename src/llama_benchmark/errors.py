class BenchmarkError(RuntimeError):
    """An expected operational benchmark failure."""


class ServerError(BenchmarkError):
    """The configured llama-server could not be used safely."""
