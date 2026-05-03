PYTHON_BUILTINS = {
    'print', 'len', 'range', 'str', 'int', 'float', 'list',
    'dict', 'set', 'tuple', 'bool', 'type', 'isinstance',
    'hasattr', 'getattr', 'setattr', 'open', 'sorted',
    'enumerate', 'zip', 'map', 'filter', 'sum', 'min', 'max',
    'abs', 'round', 'any', 'all'
}

RISK_THRESHOLDS = {'LOW': 2, 'MEDIUM': 4}
COUPLING_THRESHOLD = 3
LARGE_CLASS_THRESHOLD = 6
GOD_FILE_THRESHOLD = 10
SUPPORTED_EXTENSIONS = {'.py'}
IGNORE_DIRS = {
    '__pycache__', '.git', '.venv', 'venv',
    'node_modules', '.idea', '.vscode',
    'temp_repos'
}