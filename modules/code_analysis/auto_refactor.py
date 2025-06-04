import os
import ast
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from datetime import datetime
import subprocess

logger = logging.getLogger(__name__)

class AutoRefactor:
    """Automatically refactors Python files over 200 lines into smaller modular pieces."""
    
    def __init__(self, line_threshold: int = 200):
        self.line_threshold = line_threshold
        self.backup_dir = Path("backups/refactor")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def find_large_files(self, directory: str = ".") -> List[Tuple[str, int]]:
        """Find Python files over the line threshold."""
        large_files = []
        
        for root, dirs, files in os.walk(directory):
            # Skip certain directories
            skip_dirs = {'.git', '__pycache__', 'node_modules', 'venv', 'env', 'axis_env', 'faiss'}
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = len(f.readlines())
                            if lines > self.line_threshold:
                                large_files.append((file_path, lines))
                    except Exception as e:
                        logger.warning(f"Could not read {file_path}: {e}")
        
        return sorted(large_files, key=lambda x: x[1], reverse=True)
    
    def analyze_file_structure(self, file_path: str) -> Dict:
        """Analyze the structure of a Python file to determine how to split it."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            analysis = {
                "imports": [],
                "classes": [],
                "functions": [],
                "constants": [],
                "other": []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    analysis["imports"].extend([alias.name for alias in node.names])
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    analysis["imports"].append(module)
                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "lineno": node.lineno,
                        "end_lineno": getattr(node, 'end_lineno', node.lineno + 50),
                        "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    }
                    analysis["classes"].append(class_info)
                elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:  # Top-level functions
                    func_info = {
                        "name": node.name,
                        "lineno": node.lineno,
                        "end_lineno": getattr(node, 'end_lineno', node.lineno + 20)
                    }
                    analysis["functions"].append(func_info)
                elif isinstance(node, ast.Assign) and node.col_offset == 0:  # Top-level assignments
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            analysis["constants"].append({
                                "name": target.id,
                                "lineno": node.lineno
                            })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return {}
    
    def suggest_refactoring(self, file_path: str, analysis: Dict) -> List[Dict]:
        """Suggest how to refactor the file based on analysis."""
        suggestions = []
        
        # Group classes by functionality
        classes = analysis.get("classes", [])
        functions = analysis.get("functions", [])
        
        if len(classes) > 1:
            # Suggest splitting by classes
            for cls in classes:
                suggestions.append({
                    "type": "class_split",
                    "name": f"{cls['name'].lower()}.py",
                    "content": f"Extract {cls['name']} class",
                    "line_range": (cls["lineno"], cls["end_lineno"]),
                    "includes": [cls["name"]]
                })
        
        elif len(classes) == 1 and len(functions) > 5:
            # Large class with many functions - suggest splitting by functionality
            cls = classes[0]
            methods = cls.get("methods", [])
            
            # Group methods by common prefixes/functionality
            method_groups = self._group_methods_by_functionality(methods)
            
            for group_name, group_methods in method_groups.items():
                if len(group_methods) > 2:
                    suggestions.append({
                        "type": "method_group",
                        "name": f"{cls['name'].lower()}_{group_name}.py",
                        "content": f"Extract {group_name} methods from {cls['name']}",
                        "includes": group_methods
                    })
        
        elif len(functions) > 10:
            # Many top-level functions - group by functionality
            func_groups = self._group_functions_by_functionality([f["name"] for f in functions])
            
            for group_name, group_funcs in func_groups.items():
                suggestions.append({
                    "type": "function_group", 
                    "name": f"{group_name}.py",
                    "content": f"Extract {group_name} functions",
                    "includes": group_funcs
                })
        
        # If no clear grouping, suggest generic split
        if not suggestions:
            suggestions.append({
                "type": "generic_split",
                "name": "split_needed",
                "content": "File needs manual refactoring - too complex for automatic splitting",
                "suggestions": [
                    "Consider splitting by functionality",
                    "Extract utility functions",
                    "Separate data models from business logic",
                    "Move configuration to separate file"
                ]
            })
        
        return suggestions
    
    def _group_methods_by_functionality(self, methods: List[str]) -> Dict[str, List[str]]:
        """Group methods by common functionality based on naming patterns."""
        groups = {
            "data": [],
            "validation": [],
            "processing": [],
            "utility": [],
            "api": [],
            "database": [],
            "other": []
        }
        
        for method in methods:
            method_lower = method.lower()
            
            if any(keyword in method_lower for keyword in ['get', 'set', 'load', 'save', 'fetch']):
                groups["data"].append(method)
            elif any(keyword in method_lower for keyword in ['validate', 'check', 'verify', 'ensure']):
                groups["validation"].append(method)
            elif any(keyword in method_lower for keyword in ['process', 'transform', 'convert', 'parse']):
                groups["processing"].append(method)
            elif any(keyword in method_lower for keyword in ['format', 'clean', 'normalize', 'helper']):
                groups["utility"].append(method)
            elif any(keyword in method_lower for keyword in ['api', 'endpoint', 'route', 'request']):
                groups["api"].append(method)
            elif any(keyword in method_lower for keyword in ['db', 'database', 'query', 'insert', 'update', 'delete']):
                groups["database"].append(method)
            else:
                groups["other"].append(method)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}
    
    def _group_functions_by_functionality(self, functions: List[str]) -> Dict[str, List[str]]:
        """Group functions by common functionality based on naming patterns."""
        groups = {
            "utils": [],
            "data": [],
            "validation": [],
            "processing": [],
            "api": [],
            "helpers": []
        }
        
        for func in functions:
            func_lower = func.lower()
            
            if any(keyword in func_lower for keyword in ['util', 'helper', 'tool']):
                groups["utils"].append(func)
            elif any(keyword in func_lower for keyword in ['get', 'fetch', 'load', 'save', 'read', 'write']):
                groups["data"].append(func)
            elif any(keyword in func_lower for keyword in ['validate', 'check', 'verify', 'test']):
                groups["validation"].append(func)
            elif any(keyword in func_lower for keyword in ['process', 'transform', 'convert', 'handle']):
                groups["processing"].append(func)
            elif any(keyword in func_lower for keyword in ['api', 'request', 'response', 'endpoint']):
                groups["api"].append(func)
            else:
                groups["helpers"].append(func)
        
        return {k: v for k, v in groups.items() if v}
    
    def create_backup(self, file_path: str) -> str:
        """Create a backup of the file before refactoring."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{Path(file_path).stem}_{timestamp}.py.bak"
        backup_path = self.backup_dir / backup_name
        
        try:
            import shutil
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
            raise
    
    def generate_refactoring_report(self, directory: str = ".") -> Dict:
        """Generate a comprehensive refactoring report."""
        large_files = self.find_large_files(directory)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_files_analyzed": 0,
            "files_needing_refactoring": len(large_files),
            "total_lines_analyzed": 0,
            "files": []
        }
        
        for file_path, line_count in large_files:
            analysis = self.analyze_file_structure(file_path)
            suggestions = self.suggest_refactoring(file_path, analysis)
            
            file_report = {
                "path": file_path,
                "lines": line_count,
                "analysis": analysis,
                "suggestions": suggestions,
                "priority": self._calculate_priority(line_count, analysis)
            }
            
            report["files"].append(file_report)
            report["total_lines_analyzed"] += line_count
        
        # Add Python files count
        python_files = []
        for root, dirs, files in os.walk(directory):
            skip_dirs = {'.git', '__pycache__', 'node_modules', 'venv', 'env', 'axis_env', 'faiss'}
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        report["total_files_analyzed"] = len(python_files)
        
        return report
    
    def _calculate_priority(self, line_count: int, analysis: Dict) -> str:
        """Calculate refactoring priority based on file size and complexity."""
        classes = len(analysis.get("classes", []))
        functions = len(analysis.get("functions", []))
        
        complexity_score = classes * 2 + functions
        
        if line_count > 500 or complexity_score > 20:
            return "high"
        elif line_count > 300 or complexity_score > 10:
            return "medium"
        else:
            return "low"
    
    def auto_refactor_file(self, file_path: str, dry_run: bool = True) -> Dict:
        """Automatically refactor a file (with dry run option)."""
        result = {
            "file": file_path,
            "success": False,
            "backup_created": None,
            "files_created": [],
            "errors": []
        }
        
        try:
            # Create backup first
            if not dry_run:
                backup_path = self.create_backup(file_path)
                result["backup_created"] = backup_path
            
            # Analyze file
            analysis = self.analyze_file_structure(file_path)
            suggestions = self.suggest_refactoring(file_path, analysis)
            
            if dry_run:
                result["suggestions"] = suggestions
                result["success"] = True
                result["message"] = "Dry run completed - no files modified"
            else:
                # Implement actual refactoring based on suggestions
                result["message"] = "Automatic refactoring not yet implemented - manual refactoring required"
                result["suggestions"] = suggestions
                
        except Exception as e:
            result["errors"].append(str(e))
            logger.error(f"Error refactoring {file_path}: {e}")
        
        return result
    
    def run_refactoring_scan(self, directory: str = ".") -> Dict:
        """Run a complete refactoring scan and return actionable report."""
        logger.info(f"Starting refactoring scan of {directory}")
        
        report = self.generate_refactoring_report(directory)
        
        # Add summary statistics
        high_priority = len([f for f in report["files"] if f["priority"] == "high"])
        medium_priority = len([f for f in report["files"] if f["priority"] == "medium"])
        low_priority = len([f for f in report["files"] if f["priority"] == "low"])
        
        report["summary"] = {
            "high_priority_files": high_priority,
            "medium_priority_files": medium_priority, 
            "low_priority_files": low_priority,
            "avg_lines_per_large_file": report["total_lines_analyzed"] / max(report["files_needing_refactoring"], 1),
            "refactoring_needed": report["files_needing_refactoring"] > 0
        }
        
        logger.info(f"Scan complete: {report['files_needing_refactoring']} files need refactoring")
        
        return report


def get_auto_refactor() -> AutoRefactor:
    """Get AutoRefactor singleton instance."""
    return AutoRefactor() 