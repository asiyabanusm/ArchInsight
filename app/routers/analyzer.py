from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from pathlib import Path
import subprocess
import shutil
import uuid
import tempfile

from app.core.code_analyzer import CodebaseAnalyzer


router = APIRouter()


# Request Models
class GitHubRequest(BaseModel):
    github_url: str


class ImpactRequest(BaseModel):
    github_url: str
    function_name: str


class ClassUsageRequest(BaseModel):
    path: str
    class_name: str


class FileImpactRequest(BaseModel):
    path: str
    file_name: str


# Helper: Clone GitHub Repo
def clone_github_repo(github_url: str) -> Path:
    """Clone a GitHub repo to a temp folder"""
    
    if not github_url.startswith("https://github.com/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub URL"
        )
    
    temp_dir = Path(tempfile.gettempdir()) / "project_analyzer_repos"
    temp_dir.mkdir(exist_ok=True)
    
    repo_name = github_url.rstrip("/").split("/")[-1].replace(".git", "")
    unique_name = f"{repo_name}_{uuid.uuid4().hex[:8]}"
    clone_path = temp_dir / unique_name
    
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", github_url, str(clone_path)],
            check=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        return clone_path
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to clone: {e.stderr}"
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Clone timeout")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Git not installed")


def cleanup_repo(path: Path):
    """Delete cloned repo"""
    try:
        if path.exists():
            shutil.rmtree(path)
    except Exception as e:
        print(f"Cleanup warning: {e}")


# API Endpoints
@router.post("/analyze")
def analyze_github_repo(request: GitHubRequest) -> Dict[str, Any]:
    """Analyze a GitHub repository"""
    
    repo_path = None
    
    try:
        repo_path = clone_github_repo(request.github_url)
        
        analyzer = CodebaseAnalyzer(str(repo_path))
        result = analyzer.analyze()
        
        complexity = analyzer.calculate_complexity_score()
        ai_suggestions = analyzer.generate_ai_suggestions()
        
        return {
            "success": True,
            "github_url": request.github_url,
            "project_name": result.project_name,
            "complexity_score": complexity,
            "ai_suggestions": ai_suggestions,
            "summary": {
                "total_files": len(result.files),
                "total_functions": len(result.functions),
                "total_issues": len(result.issues)
            },
            "data": {
                "architecture": _format_architecture(result),
                "connections": _format_connections(result),
                "metrics": _format_metrics(result, analyzer),
                "issues": result.issues
            }
        }
    finally:
        if repo_path:
            cleanup_repo(repo_path)


@router.post("/architecture")
def get_architecture(request: GitHubRequest) -> Dict[str, Any]:
    """Get architecture tree"""
    
    repo_path = None
    
    try:
        repo_path = clone_github_repo(request.github_url)
        
        analyzer = CodebaseAnalyzer(str(repo_path))
        result = analyzer.analyze()
        
        return {
            "success": True,
            "github_url": request.github_url,
            "project_name": result.project_name,
            "architecture": _format_architecture(result)
        }
    finally:
        if repo_path:
            cleanup_repo(repo_path)


@router.post("/impact")
def get_impact_analysis(request: ImpactRequest) -> Dict[str, Any]:
    """Impact analysis for a function"""
    
    repo_path = None
    
    try:
        repo_path = clone_github_repo(request.github_url)
        
        analyzer = CodebaseAnalyzer(str(repo_path))
        result = analyzer.analyze()
        
        func_info = None
        target = request.function_name
        
        for name, info in result.functions.items():
            if name == target or info.name == target:
                func_info = info
                target = name
                break
        
        if not func_info:
            raise HTTPException(
                status_code=404,
                detail=f"Function not found"
            )
        
        impact = analyzer.get_impact_analysis(target)
        
        return {
            "success": True,
            "function": target,
            "file": func_info.file,
            "direct_impact": impact["direct_impact"],
            "indirect_impact": impact["indirect_impact"]
        }
    finally:
        if repo_path:
            cleanup_repo(repo_path)


@router.post("/issues")
def get_issues(request: GitHubRequest) -> Dict[str, Any]:
    """Get detected issues"""
    
    repo_path = None
    
    try:
        repo_path = clone_github_repo(request.github_url)
        
        analyzer = CodebaseAnalyzer(str(repo_path))
        result = analyzer.analyze()
        
        return {
            "success": True,
            "github_url": request.github_url,
            "total_issues": len(result.issues),
            "issues": result.issues
        }
    finally:
        if repo_path:
            cleanup_repo(repo_path)


@router.post("/connections")
def get_connections(request: GitHubRequest) -> Dict[str, Any]:
    """Get function connections"""
    
    repo_path = None
    
    try:
        repo_path = clone_github_repo(request.github_url)
        
        analyzer = CodebaseAnalyzer(str(repo_path))
        result = analyzer.analyze()
        
        return {
            "success": True,
            "github_url": request.github_url,
            "connections": _format_connections(result)
        }
    finally:
        if repo_path:
            cleanup_repo(repo_path)


@router.post("/metrics")
def get_metrics(request: GitHubRequest) -> Dict[str, Any]:
    """Get file metrics"""
    
    repo_path = None
    
    try:
        repo_path = clone_github_repo(request.github_url)
        
        analyzer = CodebaseAnalyzer(str(repo_path))
        result = analyzer.analyze()
        
        return {
            "success": True,
            "github_url": request.github_url,
            "metrics": _format_metrics(result, analyzer)
        }
    finally:
        if repo_path:
            cleanup_repo(repo_path)


@router.post("/class-usage")
def get_class_usage_endpoint(request: ClassUsageRequest) -> Dict[str, Any]:
    """Get class usage information"""
    
    repo_path = None
    
    try:
        repo_path = clone_github_repo(request.path)
        
        analyzer = CodebaseAnalyzer(str(repo_path))
        analyzer.analyze()
        
        usage = analyzer.get_class_usage(request.class_name)
        
        return {
            "success": True,
            "class_name": request.class_name,
            **usage
        }
    finally:
        if repo_path:
            cleanup_repo(repo_path)


@router.post("/file-impact")
def get_file_impact_endpoint(request: FileImpactRequest) -> Dict[str, Any]:
    """Get file impact analysis"""
    
    repo_path = None
    
    try:
        repo_path = clone_github_repo(request.path)
        
        analyzer = CodebaseAnalyzer(str(repo_path))
        analyzer.analyze()
        
        impact = analyzer.get_file_impact(request.file_name)
        
        return {
            "success": True,
            "file_name": request.file_name,
            **impact
        }
    finally:
        if repo_path:
            cleanup_repo(repo_path)


# Helper Formatters
def _format_architecture(result) -> List[Dict]:
    architecture = []
    
    for file_name, file_info in sorted(result.files.items()):
        file_data = {
            "file": file_name,
            "classes": [],
            "functions": file_info.functions
        }
        
        for class_info in file_info.classes:
            file_data["classes"].append({
                "name": class_info.name,
                "methods": class_info.methods
            })
        
        architecture.append(file_data)
    
    return architecture


def _format_connections(result) -> List[Dict]:
    connections = []
    
    for func_name, func_info in sorted(result.functions.items()):
        project_calls = []
        
        for call in func_info.calls:
            if call in result.function_to_file:
                project_calls.append({
                    "function": call,
                    "file": result.function_to_file[call]
                })
        
        if project_calls:
            connections.append({
                "function": func_info.full_name,
                "file": func_info.file,
                "calls": project_calls
            })
    
    return connections


def _format_metrics(result, analyzer) -> List[Dict]:
    metrics = []
    
    for file_name in sorted(result.files.keys()):
        file_metrics = analyzer.get_file_metrics(file_name)
        
        if file_metrics:
            metrics.append({
                "file": file_name,
                **file_metrics
            })
    
    return metrics