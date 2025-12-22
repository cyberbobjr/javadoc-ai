"""
LLM integration module for Javadoc generation.
Supports both LangChain and PydanticAI providers.
"""

import logging
from typing import Optional, Dict
from java_parser import JavaElement


logger = logging.getLogger(__name__)


class JavadocGenerator:
    """Generates Javadoc using LLM providers."""
    
    def __init__(self, provider: str, model: str, api_key: str, temperature: float = 0.3, max_tokens: int = 1000):
        """
        Initialize Javadoc generator.
        
        Args:
            provider: LLM provider ('langchain' or 'pydantic-ai')
            model: Model name (e.g., 'gpt-4', 'gpt-3.5-turbo')
            api_key: API key for the LLM service
            temperature: Temperature for generation
            max_tokens: Maximum tokens for response
        """
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.llm = None
        
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM based on the provider."""
        try:
            if self.provider == 'langchain':
                self._initialize_langchain()
            elif self.provider == 'pydantic-ai':
                self._initialize_pydantic_ai()
            else:
                logger.error(f"Unsupported provider: {self.provider}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
    
    def _initialize_langchain(self):
        """Initialize LangChain LLM."""
        try:
            from langchain_openai import ChatOpenAI
            from langchain.prompts import ChatPromptTemplate
            from langchain.schema.output_parser import StrOutputParser
            
            self.llm = ChatOpenAI(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                api_key=self.api_key
            )
            
            # Create a prompt template for Javadoc generation
            self.prompt_template = ChatPromptTemplate.from_messages([
                ("system", """You are an expert Java developer specializing in writing clear, 
                comprehensive Javadoc comments. Generate professional Javadoc comments that:
                - Start with a concise summary of what the element does
                - Include @param tags for all parameters
                - Include @return tag for non-void methods
                - Include @throws tags for declared exceptions
                - Follow standard Javadoc conventions
                - Are concise but informative
                - Do NOT include the opening /** or closing */ markers
                """),
                ("user", """Generate a Javadoc comment for this Java {element_type}:

File: {file_path}
{element_type}: {element_name}
Signature: {signature}

Code context:
{code_context}

Generate only the Javadoc content without /** and */ markers.""")
            ])
            
            self.chain = self.prompt_template | self.llm | StrOutputParser()
            logger.info("LangChain LLM initialized successfully")
            
        except ImportError as e:
            logger.error(f"Failed to import LangChain: {e}")
            logger.error("Install with: pip install langchain langchain-openai")
        except Exception as e:
            logger.error(f"Failed to initialize LangChain: {e}")
    
    def _initialize_pydantic_ai(self):
        """Initialize PydanticAI LLM."""
        try:
            # Note: PydanticAI is a newer library with different API
            # Currently falling back to LangChain for compatibility
            # TODO: Implement native PydanticAI support when API stabilizes
            logger.warning("PydanticAI support is not yet implemented, using LangChain")
            self._initialize_langchain()
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
    
    def generate_javadoc(self, element: JavaElement, file_path: str, code_context: str) -> Optional[str]:
        """
        Generate Javadoc for a Java element.
        
        Args:
            element: JavaElement to document
            file_path: Path to the file
            code_context: Code context around the element
        
        Returns:
            Generated Javadoc string or None if failed
        """
        if not self.llm:
            logger.error("LLM not initialized")
            return None
        
        try:
            if self.provider == 'langchain':
                return self._generate_with_langchain(element, file_path, code_context)
            elif self.provider == 'pydantic-ai':
                return self._generate_with_pydantic_ai(element, file_path, code_context)
        except Exception as e:
            logger.error(f"Failed to generate Javadoc: {e}")
            return None
    
    def _generate_with_langchain(self, element: JavaElement, file_path: str, code_context: str) -> Optional[str]:
        """Generate Javadoc using LangChain."""
        try:
            response = self.chain.invoke({
                "element_type": element.element_type,
                "file_path": file_path,
                "element_name": element.name,
                "signature": element.signature,
                "code_context": code_context
            })
            
            # Clean up the response
            javadoc = response.strip()
            
            # Ensure proper formatting
            lines = javadoc.split('\n')
            formatted_lines = ['/**']
            for line in lines:
                if line.strip():
                    formatted_lines.append(' * ' + line.strip())
                else:
                    formatted_lines.append(' *')
            formatted_lines.append(' */')
            
            return '\n'.join(formatted_lines)
            
        except Exception as e:
            logger.error(f"LangChain generation failed: {e}")
            return None
    
    def _generate_with_pydantic_ai(self, element: JavaElement, file_path: str, code_context: str) -> Optional[str]:
        """Generate Javadoc using PydanticAI."""
        # Fallback to LangChain for now
        return self._generate_with_langchain(element, file_path, code_context)
    
    def generate_batch(self, elements: list, file_path: str, content: str, max_elements: int = 0) -> Dict[str, str]:
        """
        Generate Javadoc for multiple elements in batch.
        
        Args:
            elements: List of JavaElement objects
            file_path: Path to the file
            content: Full file content
            max_elements: Maximum number of elements to process (0 = unlimited)
        
        Returns:
            Dictionary mapping element names to generated Javadoc
        """
        results = {}
        
        elements_to_process = elements[:max_elements] if max_elements > 0 else elements
        
        from java_parser import JavaParser
        parser = JavaParser()
        
        for i, element in enumerate(elements_to_process, 1):
            logger.info(f"Generating Javadoc for {element.name} ({i}/{len(elements_to_process)})")
            
            # Extract code context
            code_context = parser.extract_code_context(content, element)
            
            # Generate Javadoc
            javadoc = self.generate_javadoc(element, file_path, code_context)
            
            if javadoc:
                results[f"{element.element_type}:{element.name}:{element.line_number}"] = javadoc
            else:
                logger.warning(f"Failed to generate Javadoc for {element.name}")
        
        return results
