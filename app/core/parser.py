import ast
from pathlib import Path
from typing import Optional

from app.core.models import FunctionInfo, ClassInfo, FileInfo
from app.core.constants import PYTHON_BUILTINS


class ASTParser:
    def __init__(self):
        self.builtins = PYTHON_BUILTINS
    
    def parse_file(self, file_path: Path, base_path: Path) -> Optional[FileInfo]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            rel_path = str(file_path.relative_to(base_path))
            
            return self._extract_file_info(tree, rel_path)
            
        except SyntaxError:
            return None
        except Exception:
            return None
    
    def _extract_file_info(self, tree: ast.Module, file_name: str) -> FileInfo:
        file_info = FileInfo(path=file_name)
        
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_info = self._parse_class(node)
                file_info.classes.append(class_info)
                
            elif isinstance(node, ast.FunctionDef):
                file_info.functions.append(node.name)
                
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    file_info.imports.append(alias.name)
                    
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    file_info.imports.append(node.module)
        
        return file_info
    
    def _parse_class(self, node: ast.ClassDef) -> ClassInfo:
        class_info = ClassInfo(
            name=node.name,
            line_number=node.lineno
        )
        
        for base in node.bases:
            if isinstance(base, ast.Name):
                class_info.bases.append(base.id)
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                class_info.methods.append(item.name)
        
        return class_info
    
    def extract_function_details(self, file_path: Path, base_path: Path) -> dict:
        functions = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            rel_path = str(file_path.relative_to(base_path))
            
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            func_info = self._create_function_info(
                                item, rel_path, node.name
                            )
                            functions[func_info.full_name] = func_info
                
                elif isinstance(node, ast.FunctionDef):
                    func_info = self._create_function_info(node, rel_path)
                    functions[func_info.name] = func_info
            
            return functions
            
        except Exception:
            return {}
    
    def _create_function_info(
        self, 
        node: ast.FunctionDef, 
        file_name: str,
        class_name: str = None
    ) -> FunctionInfo:
        func_info = FunctionInfo(
            name=node.name,
            file=file_name,
            line_number=node.lineno,
            class_name=class_name
        )
        
        func_info.calls = self._extract_calls(node)
        
        return func_info
    
    def _extract_calls(self, node: ast.FunctionDef) -> set:
        calls = set()
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                call_name = self._get_call_name(child.func)
                
                if call_name and call_name not in self.builtins:
                    calls.add(call_name)
        
        return calls
    
    def _get_call_name(self, node) -> Optional[str]:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return None