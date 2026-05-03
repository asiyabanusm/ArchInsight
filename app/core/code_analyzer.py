from pathlib import Path
from typing import Dict, List, Set, Any

from app.core.models import AnalysisResult, FunctionInfo
from app.core.parser import ASTParser
from app.core.constants import (
    IGNORE_DIRS, 
    SUPPORTED_EXTENSIONS,
    RISK_THRESHOLDS,
    COUPLING_THRESHOLD,
    LARGE_CLASS_THRESHOLD,
    GOD_FILE_THRESHOLD
)


class CodebaseAnalyzer:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self.project_name = self.repo_path.name
        self.parser = ASTParser()
        self.result = AnalysisResult(project_name=self.project_name)
        
    def analyze(self) -> AnalysisResult:
        python_files = self._get_python_files()
        
        if not python_files:
            return self.result
        
        self._parse_all_files(python_files)
        self._extract_all_functions(python_files)
        self._detect_issues()
        
        return self.result
    
    def _get_python_files(self) -> List[Path]:
        files = []
        
        for file_path in self.repo_path.rglob("*"):
            if any(ignored in file_path.parts for ignored in IGNORE_DIRS):
                continue
            
            if file_path.suffix in SUPPORTED_EXTENSIONS:
                files.append(file_path)
        
        return sorted(files)
    
    def _parse_all_files(self, files: List[Path]):
        for file_path in files:
            file_info = self.parser.parse_file(file_path, self.repo_path)
            
            if file_info:
                self.result.files[file_info.path] = file_info
    
    def _extract_all_functions(self, files: List[Path]):
        for file_path in files:
            functions = self.parser.extract_function_details(
                file_path, self.repo_path
            )
            
            for func_name, func_info in functions.items():
                self.result.functions[func_name] = func_info
                self.result.function_to_file[func_name] = func_info.file
    
    def _detect_issues(self):
        issues = []
        
        for func_name, func_info in self.result.functions.items():
            modules = self._get_connected_modules(func_info)
            if len(modules) > COUPLING_THRESHOLD:
                issues.append(
                    f"High Coupling: {func_name}() connects to {len(modules)} modules"
                )
        
        for file_info in self.result.files.values():
            for class_info in file_info.classes:
                if class_info.method_count > LARGE_CLASS_THRESHOLD:
                    issues.append(
                        f"Large Class: {class_info.name} has {class_info.method_count} methods"
                    )
        
        for file_name, file_info in self.result.files.items():
            if file_info.total_functions > GOD_FILE_THRESHOLD:
                issues.append(
                    f"God File: {file_name} has {file_info.total_functions} functions"
                )
        
        self.result.issues = issues
    
    def _get_connected_modules(self, func_info: FunctionInfo) -> Set[str]:
        modules = set()
        
        for call in func_info.calls:
            if call in self.result.function_to_file:
                call_file = self.result.function_to_file[call]
                if call_file != func_info.file:
                    modules.add(call_file)
        
        return modules
    
    def get_impact_analysis(self, func_name: str) -> Dict[str, List[str]]:
        if func_name not in self.result.functions:
            return {"direct_impact": [], "indirect_impact": []}
        
        func_info = self.result.functions[func_name]
        
        direct = []
        for name, info in self.result.functions.items():
            if func_name in info.calls or func_info.name in info.calls:
                if name != func_name:
                    direct.append(name)
        
        indirect = list(func_info.calls)
        
        return {
            "direct_impact": direct,
            "indirect_impact": indirect
        }
    
    def get_file_metrics(self, file_name: str) -> dict:
        if file_name not in self.result.files:
            return None
        
        file_info = self.result.files[file_name]
        
        external_calls = 0
        for func_name, func_info in self.result.functions.items():
            if func_info.file == file_name:
                external_calls += len(func_info.calls)
        
        if external_calls < RISK_THRESHOLDS['LOW']:
            risk = "LOW"
        elif external_calls <= RISK_THRESHOLDS['MEDIUM']:
            risk = "MEDIUM"
        else:
            risk = "HIGH"
        
        return {
            "total_functions": file_info.total_functions,
            "total_classes": file_info.total_classes,
            "external_calls": external_calls,
            "risk_level": risk
        }
    
    def calculate_complexity_score(self) -> Dict[str, Any]:
        """Calculate overall code complexity and quality score"""
        
        if not self.result.files:
            return {
                "overall_score": 0,
                "grade": "N/A",
                "complexity": "N/A",
                "details": {}
            }
        
        # Metrics for scoring
        total_files = len(self.result.files)
        total_functions = len(self.result.functions)
        total_issues = len(self.result.issues)
        
        # Calculate average functions per file
        avg_functions_per_file = total_functions / total_files if total_files > 0 else 0
        
        # Count high-risk files
        high_risk_files = 0
        for file_name in self.result.files.keys():
            metrics = self.get_file_metrics(file_name)
            if metrics and metrics['risk_level'] == 'HIGH':
                high_risk_files += 1
        
        # Calculate scores (0-100 scale)
        
        # 1. Issue Score (40 points max)
        issue_ratio = total_issues / total_functions if total_functions > 0 else 0
        issue_score = max(0, 40 - (issue_ratio * 100))
        
        # 2. Modularity Score (30 points max)
        if avg_functions_per_file <= 5:
            modularity_score = 30
        elif avg_functions_per_file <= 10:
            modularity_score = 25
        elif avg_functions_per_file <= 15:
            modularity_score = 15
        else:
            modularity_score = 5
        
        # 3. Risk Score (30 points max)
        risk_ratio = high_risk_files / total_files if total_files > 0 else 0
        risk_score = max(0, 30 - (risk_ratio * 100))
        
        # Overall score
        overall_score = min(100, int(issue_score + modularity_score + risk_score))
        
        # Grade assignment
        if overall_score >= 90:
            grade = "A+"
            complexity = "Excellent"
        elif overall_score >= 80:
            grade = "A"
            complexity = "Very Good"
        elif overall_score >= 70:
            grade = "B"
            complexity = "Good"
        elif overall_score >= 60:
            grade = "C"
            complexity = "Fair"
        elif overall_score >= 50:
            grade = "D"
            complexity = "Poor"
        else:
            grade = "F"
            complexity = "Needs Improvement"
        
        return {
            "overall_score": overall_score,
            "grade": grade,
            "complexity": complexity,
            "details": {
                "total_files": total_files,
                "total_functions": total_functions,
                "total_issues": total_issues,
                "avg_functions_per_file": round(avg_functions_per_file, 2),
                "high_risk_files": high_risk_files,
                "issue_score": round(issue_score, 1),
                "modularity_score": round(modularity_score, 1),
                "risk_score": round(risk_score, 1)
            }
        }
    def generate_ai_suggestions(self) -> List[Dict[str, str]]:
        """Generate AI-powered code improvement suggestions"""
        
        suggestions = []
        
        # Analyze issues and generate suggestions
        for issue in self.result.issues:
            if "High Coupling" in issue:
                func_name = issue.split(":")[1].split("()")[0].strip()
                suggestions.append({
                    "type": "refactoring",
                    "severity": "high",
                    "title": "Reduce Coupling",
                    "description": f"Function {func_name}() is highly coupled. Consider using dependency injection or facade pattern.",
                    "suggestion": "Extract shared dependencies into a separate service class",
                    "impact": "Improves maintainability and testability"
                })
            
            elif "Large Class" in issue:
                class_name = issue.split(":")[1].split(" has")[0].strip()
                suggestions.append({
                    "type": "design",
                    "severity": "medium",
                    "title": "Split Large Class",
                    "description": f"Class {class_name} has too many methods. Consider applying Single Responsibility Principle.",
                    "suggestion": "Split into smaller, focused classes using composition",
                    "impact": "Easier to understand, test, and maintain"
                })
            
            elif "God File" in issue:
                file_name = issue.split(":")[1].split(" has")[0].strip()
                suggestions.append({
                    "type": "architecture",
                    "severity": "medium",
                    "title": "Modularize File",
                    "description": f"File {file_name} contains too many functions.",
                    "suggestion": "Split into multiple focused modules by domain/responsibility",
                    "impact": "Better organization and code discoverability"
                })
        
        # Code quality suggestions based on metrics
        total_files = len(self.result.files)
        total_functions = len(self.result.functions)
        
        if total_functions > 0:
            avg_complexity = total_functions / total_files if total_files > 0 else 0
            
            if avg_complexity > 15:
                suggestions.append({
                    "type": "best-practice",
                    "severity": "low",
                    "title": "Consider Adding Documentation",
                    "description": "Project has high function density. Good documentation becomes crucial.",
                    "suggestion": "Add docstrings to all public functions and classes",
                    "impact": "Improves onboarding and maintenance"
                })
        
        # Check for lack of modularity
        files_with_no_classes = sum(1 for f in self.result.files.values() if len(f.classes) == 0)
        if files_with_no_classes > total_files * 0.7:
            suggestions.append({
                "type": "design",
                "severity": "low",
                "title": "Consider Object-Oriented Design",
                "description": "Most files use procedural programming. OOP might improve structure.",
                "suggestion": "Identify related functions and group them into classes",
                "impact": "Better encapsulation and code reusability"
            })
        
        # Default suggestion if code is excellent
        if not suggestions:
            suggestions.append({
                "type": "compliment",
                "severity": "info",
                "title": "Excellent Code Quality! 🎉",
                "description": "Your code follows best practices with minimal issues.",
                "suggestion": "Continue maintaining this quality. Consider adding automated tests if not present.",
                "impact": "Sustained high quality and reliability"
            })
        
        return suggestions
    def get_class_usage(self, class_name: str) -> Dict[str, Any]:
        """Find where a class is used"""
        
        used_by_functions = []
        used_by_classes = []
        
        # Check functions that might use this class
        for func_name, func_info in self.result.functions.items():
            # Check if class name appears in function calls or dependencies
            if class_name in str(func_info.calls):
                used_by_functions.append({
                    "function": func_name,
                    "file": func_info.file
                })
        
        # Check class inheritance
        for file_info in self.result.files.values():
            for cls in file_info.classes:
                if class_name in cls.bases:
                    used_by_classes.append({
                        "class": cls.name,
                        "file": file_info.path,
                        "relationship": "inherits"
                    })
        
        return {
            "used_by_functions": used_by_functions,
            "used_by_classes": used_by_classes,
            "total_usage": len(used_by_functions) + len(used_by_classes)
        }
    
    def get_file_impact(self, file_name: str) -> Dict[str, Any]:
        """Analyze impact if a file changes"""
        
        if file_name not in self.result.files:
            return {"error": "File not found"}
        
        file_info = self.result.files[file_name]
        
        # Find all files that import/use functions from this file
        dependent_files = set()
        affected_functions = []
        
        # Get all functions in this file
        file_functions = set(file_info.functions)
        for cls in file_info.classes:
            for method in cls.methods:
                file_functions.add(f"{cls.name}.{method}")
        
        # Check which other functions call functions in this file
        for func_name, func_info in self.result.functions.items():
            if func_info.file != file_name:  # Different file
                for call in func_info.calls:
                    if call in file_functions or any(call in f for f in file_functions):
                        dependent_files.add(func_info.file)
                        affected_functions.append({
                            "function": func_name,
                            "file": func_info.file,
                            "calls": call
                        })
        
        return {
            "dependent_files": list(dependent_files),
            "affected_functions": affected_functions,
            "impact_level": "HIGH" if len(dependent_files) > 3 else "MEDIUM" if len(dependent_files) > 1 else "LOW",
            "total_dependents": len(dependent_files)
        }