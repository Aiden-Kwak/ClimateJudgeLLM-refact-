from dataclasses import dataclass
from typing import List, Any

@dataclass
class QuestionResult:
    question: str
    response: str
    evidence: List[Any]

@dataclass
class JuryDocument:
    introduction: str
    questions: List[QuestionResult]
    conclusion: str