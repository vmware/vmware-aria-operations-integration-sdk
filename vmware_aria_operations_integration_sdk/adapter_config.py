from typing import Any
from typing import Callable
from typing import Dict
from typing import List


class Question:
    def __init__(self, key: str, prompt: Callable, *args: Any, **kwargs: Any) -> None:
        self.key = key
        self.prompt = prompt
        self.prompt_args = args
        self.prompt_kwargs = kwargs

    def ask(self) -> Any:
        return self.prompt(*self.prompt_args, **self.prompt_kwargs)


class AdapterConfig:
    def __init__(self, language: str, questions: List[Question] = []) -> None:
        self.language = language
        self.values: Dict[str, Any] = dict()
        self.questions = questions

    def prompt_config_values(self) -> None:
        for question in self.questions:
            self.values[question.key] = question.ask()
