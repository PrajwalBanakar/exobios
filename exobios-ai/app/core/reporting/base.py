from abc import ABC, abstractmethod

from schemas.step import StepResult


class Reporter(ABC):
    @abstractmethod
    def report(self, result: StepResult) -> None:
        ...