from core.reporting.base import Reporter
from core.reporting.file_reporting import FileReporter

reporter: Reporter = FileReporter()

__all__ = ["Reporter", "FileReporter", "reporter"]