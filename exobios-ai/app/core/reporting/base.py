from abc import ABC, abstractmethod
from schemas.step import StepResult

class Reporting(ABC):
    @abstractmethod
    def report(self, StepResult) -> None:
        ...