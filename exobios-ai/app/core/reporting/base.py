from abc import ABC, abstractmethod

from schemas.step_result import StepResult


class Reporter(ABC):
    @abstractmethod
    def report(self, result: StepResult) -> None:
        ...