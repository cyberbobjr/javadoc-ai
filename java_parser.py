"""
Java code parser module for Javadoc automation.
Parses Java files to identify classes and methods that need documentation.
"""

import re
import logging
from typing import List, Dict, Tuple
from pathlib import Path
import javalang


logger = logging.getLogger(__name__)


class JavaElement:
    """Represents a Java code element (class or method)."""
    
    def __init__(self, element_type: str, name: str, signature: str, line_number: int, has_javadoc: bool):
        self.element_type = element_type  # 'class' or 'method'
        self.name = name
        self.signature = signature
        self.line_number = line_number
        self.has_javadoc = has_javadoc
    
    def __repr__(self):
        return f"JavaElement({self.element_type}, {self.name}, line {self.line_number}, javadoc={self.has_javadoc})"


class JavaParser:
    """Parses Java files to extract classes and methods."""
    
    def __init__(self, exclude_patterns: List[str] = None):
        """
        Initialize Java parser.
        
        Args:
            exclude_patterns: List of glob patterns to exclude (e.g., test files)
        """
        self.exclude_patterns = exclude_patterns or []
    
    def should_exclude(self, file_path: str) -> bool:
        """
        Check if a file should be excluded based on patterns.
        
        Args:
            file_path: Path to the file
        
        Returns:
            True if file should be excluded
        """
        path = Path(file_path)
        for pattern in self.exclude_patterns:
            if path.match(pattern):
                logger.debug(f"Excluding {file_path} (matches pattern {pattern})")
                return True
        return False
    
    def parse_file(self, file_path: str, content: str) -> Dict[str, List[JavaElement]]:
        """
        Parse a Java file to extract classes and methods.
        
        Args:
            file_path: Path to the file (for logging)
            content: File content
        
        Returns:
            Dictionary with 'classes' and 'methods' keys containing lists of JavaElement
        """
        result = {
            'classes': [],
            'methods': []
        }
        
        try:
            # Try to parse with javalang
            tree = javalang.parse.parse(content)
            lines = content.split('\n')
            
            # Extract classes
            for path, node in tree.filter(javalang.tree.ClassDeclaration):
                javadoc = self._has_javadoc_before_line(lines, node.position.line - 1 if node.position else 0)
                element = JavaElement(
                    element_type='class',
                    name=node.name,
                    signature=f"class {node.name}",
                    line_number=node.position.line if node.position else 0,
                    has_javadoc=javadoc
                )
                result['classes'].append(element)
            
            # Extract interfaces
            for path, node in tree.filter(javalang.tree.InterfaceDeclaration):
                javadoc = self._has_javadoc_before_line(lines, node.position.line - 1 if node.position else 0)
                element = JavaElement(
                    element_type='class',
                    name=node.name,
                    signature=f"interface {node.name}",
                    line_number=node.position.line if node.position else 0,
                    has_javadoc=javadoc
                )
                result['classes'].append(element)
            
            # Extract methods
            for path, node in tree.filter(javalang.tree.MethodDeclaration):
                javadoc = self._has_javadoc_before_line(lines, node.position.line - 1 if node.position else 0)
                # Handle complex parameter types safely
                params = []
                for p in (node.parameters or []):
                    param_type = str(p.type) if hasattr(p, 'type') else 'Object'
                    params.append(f"{param_type} {p.name}")
                params_str = ', '.join(params)
                signature = f"{node.return_type.name if node.return_type else 'void'} {node.name}({params_str})"
                element = JavaElement(
                    element_type='method',
                    name=node.name,
                    signature=signature,
                    line_number=node.position.line if node.position else 0,
                    has_javadoc=javadoc
                )
                result['methods'].append(element)
            
            logger.debug(f"Parsed {file_path}: {len(result['classes'])} classes, {len(result['methods'])} methods")
            
        except javalang.parser.JavaSyntaxError as e:
            logger.warning(f"Syntax error parsing {file_path}: {e}")
            # Fallback to regex-based parsing
            result = self._parse_with_regex(content)
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            result = self._parse_with_regex(content)
        
        return result
    
    def _has_javadoc_before_line(self, lines: List[str], line_num: int) -> bool:
        """
        Check if there's a Javadoc comment before a specific line.
        
        Args:
            lines: List of file lines
            line_num: Line number to check (0-indexed)
        
        Returns:
            True if Javadoc comment found
        """
        if line_num <= 0 or line_num >= len(lines):
            return False
        
        # Check previous few lines for Javadoc
        for i in range(max(0, line_num - 10), line_num):
            line = lines[i].strip()
            if line.startswith('/**'):
                return True
            if line and not line.startswith('*') and not line.startswith('//') and not line.startswith('@'):
                # Found non-comment, non-annotation line
                break
        
        return False
    
    def _parse_with_regex(self, content: str) -> Dict[str, List[JavaElement]]:
        """
        Fallback regex-based parsing when javalang fails.
        
        Args:
            content: File content
        
        Returns:
            Dictionary with 'classes' and 'methods' keys
        """
        result = {
            'classes': [],
            'methods': []
        }
        
        lines = content.split('\n')
        
        # Simple regex patterns
        class_pattern = re.compile(r'^\s*(?:public|private|protected)?\s*(?:abstract|final)?\s*(class|interface|enum)\s+(\w+)')
        method_pattern = re.compile(r'^\s*(?:public|private|protected)?\s*(?:static|final|abstract)?\s*(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\([^)]*\)')
        
        for i, line in enumerate(lines, 1):
            # Check for class/interface
            class_match = class_pattern.search(line)
            if class_match:
                javadoc = self._has_javadoc_before_line(lines, i - 2)
                element = JavaElement(
                    element_type='class',
                    name=class_match.group(2),
                    signature=f"{class_match.group(1)} {class_match.group(2)}",
                    line_number=i,
                    has_javadoc=javadoc
                )
                result['classes'].append(element)
            
            # Check for method
            method_match = method_pattern.search(line)
            if method_match and '{' in line:
                javadoc = self._has_javadoc_before_line(lines, i - 2)
                element = JavaElement(
                    element_type='method',
                    name=method_match.group(1),
                    signature=line.strip(),
                    line_number=i,
                    has_javadoc=javadoc
                )
                result['methods'].append(element)
        
        return result
    
    def get_elements_needing_documentation(self, file_path: str, content: str) -> List[JavaElement]:
        """
        Get list of classes and methods that need Javadoc.
        
        Args:
            file_path: Path to the file
            content: File content
        
        Returns:
            List of JavaElement objects without Javadoc
        """
        if self.should_exclude(file_path):
            return []
        
        parsed = self.parse_file(file_path, content)
        
        elements_needing_doc = []
        for element in parsed['classes'] + parsed['methods']:
            if not element.has_javadoc:
                elements_needing_doc.append(element)
        
        return elements_needing_doc
    
    def extract_code_context(self, content: str, element: JavaElement, context_lines: int = 10) -> str:
        """
        Extract code context around a Java element.
        
        Args:
            content: File content
            element: JavaElement to extract context for
            context_lines: Number of lines before/after to include
        
        Returns:
            Code context as string
        """
        lines = content.split('\n')
        start = max(0, element.line_number - context_lines - 1)
        end = min(len(lines), element.line_number + context_lines)
        
        return '\n'.join(lines[start:end])
    
    def insert_javadoc(self, content: str, element: JavaElement, javadoc: str) -> str:
        """
        Insert Javadoc comment before a Java element.
        
        Args:
            content: Original file content
            element: JavaElement to document
            javadoc: Javadoc comment to insert
        
        Returns:
            Modified file content
        """
        lines = content.split('\n')
        
        # Ensure javadoc has proper format
        if not javadoc.startswith('/**'):
            javadoc = '/**\n' + javadoc
        if not javadoc.endswith('*/'):
            javadoc = javadoc + '\n */'
        
        # Find the correct line to insert (considering existing annotations)
        insert_line = element.line_number - 1
        while insert_line > 0:
            line = lines[insert_line - 1].strip()
            if line.startswith('@'):
                insert_line -= 1
            else:
                break
        
        # Get indentation from the element line
        element_line = lines[element.line_number - 1] if element.line_number <= len(lines) else ""
        indent = len(element_line) - len(element_line.lstrip())
        
        # Format javadoc with proper indentation
        javadoc_lines = javadoc.split('\n')
        indented_javadoc = '\n'.join([' ' * indent + line for line in javadoc_lines])
        
        # Insert javadoc
        lines.insert(insert_line, indented_javadoc)
        
        return '\n'.join(lines)
