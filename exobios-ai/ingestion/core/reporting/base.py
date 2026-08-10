from abc import ABC, abstractmethod
from schemas.step_result import StepResult

# interface equivalent to java
class Reporter(ABC):
    @abstractmethod
    def report(self, result: StepResult) -> None:
        ...