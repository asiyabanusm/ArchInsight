from dataclasses import dataclass, field
from typing import List, Set, Optional


@dataclass
class FunctionInfo:
    name: str
    file: str
    line_number: int = 0
    calls: Set[str] = field(default_factory=set)
    class_name: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        if self.class_name:
            return f"{self.class_name}.{self.name}"
        return self.name
    
    @property
    def display_name(self) -> str:
        return f"{self.file}:{self.full_name}()"


@dataclass
class ClassInfo:
    name: str
    line_number: int = 0
    methods: List[str] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    
    @property
    def method_count(self) -> int:
        return len(self.methods)


@dataclass
class FileInfo:
    path: str
    classes: List[ClassInfo] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    
    @property
    def total_functions(self) -> int:
        method_count = sum(c.method_count for c in self.classes)
        return len(self.functions) + method_count
    
    @property
    def total_classes(self) -> int:
        return len(self.classes)


@dataclass
class AnalysisResult:
    project_name: str
    files: dict = field(default_factory=dict)
    functions: dict = field(default_factory=dict)
    function_to_file: dict = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)