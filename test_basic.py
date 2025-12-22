"""
Basic tests for the Javadoc automation modules.
These tests verify the core logic without requiring external services.
"""

import unittest
import tempfile
import os
from pathlib import Path


class TestJavaParser(unittest.TestCase):
    """Test the Java parser module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Import here to avoid dependency issues
        try:
            from java_parser import JavaParser, JavaElement
            self.JavaParser = JavaParser
            self.JavaElement = JavaElement
        except ImportError as e:
            self.skipTest(f"Dependencies not installed: {e}")
    
    def test_exclude_patterns(self):
        """Test file exclusion patterns."""
        parser = self.JavaParser(exclude_patterns=["**/test/**", "**/*Test.java"])
        
        self.assertTrue(parser.should_exclude("src/test/MyTest.java"))
        self.assertTrue(parser.should_exclude("src/main/java/MyClassTest.java"))
        self.assertFalse(parser.should_exclude("src/main/java/MyClass.java"))
    
    def test_javadoc_detection(self):
        """Test Javadoc comment detection."""
        parser = self.JavaParser()
        
        # Sample Java code with and without Javadoc
        java_code = '''
package com.example;

/**
 * This class has Javadoc.
 */
public class DocumentedClass {
    
    /**
     * This method has Javadoc.
     */
    public void documentedMethod() {
        // implementation
    }
    
    // This method does not have Javadoc
    public void undocumentedMethod() {
        // implementation
    }
}
'''
        
        result = parser.parse_file("Test.java", java_code)
        
        # We should find both methods and the class
        self.assertIn('classes', result)
        self.assertIn('methods', result)
    
    def test_insert_javadoc(self):
        """Test Javadoc insertion."""
        parser = self.JavaParser()
        
        java_code = '''public class MyClass {
    public void myMethod() {
        System.out.println("Hello");
    }
}'''
        
        element = self.JavaElement(
            element_type='method',
            name='myMethod',
            signature='void myMethod()',
            line_number=2,
            has_javadoc=False
        )
        
        javadoc = """/**
 * This is a test method.
 */"""
        
        result = parser.insert_javadoc(java_code, element, javadoc)
        
        # Check that Javadoc was inserted
        self.assertIn('/**', result)
        self.assertIn('This is a test method', result)


class TestStateManager(unittest.TestCase):
    """Test the state manager module."""
    
    def setUp(self):
        """Set up test fixtures."""
        try:
            from state_manager import StateManager
            self.StateManager = StateManager
        except ImportError as e:
            self.skipTest(f"Dependencies not installed: {e}")
        
        # Create temporary state file
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.temp_dir, "test_state.json")
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.state_file):
            os.remove(self.state_file)
        os.rmdir(self.temp_dir)
    
    def test_first_run_detection(self):
        """Test first run detection."""
        manager = self.StateManager(self.state_file, enabled=True)
        
        # Should be first run
        self.assertTrue(manager.is_first_run())
        
        # After update, should not be first run
        manager.update_after_run("commit123", [], {})
        self.assertFalse(manager.is_first_run())
    
    def test_state_persistence(self):
        """Test that state persists between instances."""
        manager1 = self.StateManager(self.state_file, enabled=True)
        manager1.update_after_run("commit456", ["file1.java"], {'total_files': 1})
        
        # Create new instance
        manager2 = self.StateManager(self.state_file, enabled=True)
        
        # Should load previous state
        self.assertFalse(manager2.is_first_run())
        self.assertEqual(manager2.get_last_commit(), "commit456")


class TestConfigurationTemplate(unittest.TestCase):
    """Test the configuration template."""
    
    def test_config_template_valid(self):
        """Test that config template is valid YAML."""
        import yaml
        
        config_path = "config.yaml.template"
        self.assertTrue(os.path.exists(config_path), "config.yaml.template not found")
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check required sections
        required_sections = ['gitlab', 'llm', 'email', 'processing', 'state', 'logging']
        for section in required_sections:
            self.assertIn(section, config, f"Missing required section: {section}")
        
        # Check GitLab settings
        gitlab_keys = ['access_token', 'repo_url', 'branch', 'clone_dir']
        for key in gitlab_keys:
            self.assertIn(key, config['gitlab'], f"Missing GitLab setting: {key}")
        
        # Check LLM settings
        llm_keys = ['provider', 'model', 'api_key', 'temperature', 'max_tokens']
        for key in llm_keys:
            self.assertIn(key, config['llm'], f"Missing LLM setting: {key}")
        
        # Check Email settings
        email_keys = ['smtp_server', 'smtp_port', 'from_email', 'password', 'to_emails']
        for key in email_keys:
            self.assertIn(key, config['email'], f"Missing Email setting: {key}")


class TestRequirements(unittest.TestCase):
    """Test the requirements file."""
    
    def test_requirements_file_exists(self):
        """Test that requirements.txt exists and is readable."""
        self.assertTrue(os.path.exists("requirements.txt"), "requirements.txt not found")
        
        with open("requirements.txt", 'r') as f:
            requirements = f.read()
        
        # Check for essential dependencies
        essential = ['PyYAML', 'GitPython', 'langchain', 'javalang']
        for dep in essential:
            self.assertIn(dep, requirements, f"Missing dependency: {dep}")


if __name__ == '__main__':
    unittest.main()
