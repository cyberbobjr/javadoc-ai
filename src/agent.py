from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from .config import LLMConfig


class JavaDocAgent:
    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
        self.model_name = llm_config.model_name
        
        # Determine model
        if self.llm_config.base_url:
            # If base_url is provided, we assume an OpenAI-compatible endpoint
            # We use OpenAIModel with the provided base_url and api_key
            model = OpenAIModel(
                self.model_name,
                provider=OpenAIProvider(
                    base_url=self.llm_config.base_url,
                    api_key=self.llm_config.api_key.get_secret_value()
                )
            )
            # Note: For internal LLMs, api_key might be dummy, but we pass it if it's there.
        else:
            # Default behavior (Gemini or string-based inference)
            # PydanticAI will infer from string if we pass string
            model = self.model_name

        self.agent = Agent(
            model,
            system_prompt=(
                "You are a Senior Java Developer specialized in documentation. "
                "Your task is to add Javadoc to the provided Java code. "
                "1. Add Javadoc for the class, all enums, interfaces, and methods (public and private). "
                "2. Do NOT modify any logic or implementation. Only add comments. "
                "3. Use standard Javadoc tags (@param, @return, @throws, etc.). "
                "4. Return the COMPLETE source code with the Javadoc inserted. "
                "5. Ensure the code is syntactically correct and identical to the input except for the Javadoc. "
                "6. IMPORTANT: Do NOT wrap the output in Markdown code blocks (e.g., ```java). Return ONLY the raw Java code."
            )
        )

    def generate_javadoc(self, file_content: str) -> str:
        """
        Generate Javadoc for the given Java file content.
        """
        # Basic pre-check to avoid sending empty or trivial files to LLM
        # This prevents the LLM from hallucinating conversational responses for "package only" files
        stripped_content = file_content.strip()
        if not stripped_content or len(stripped_content) < self.llm_config.min_file_size:
            # If really short (just package declaration?), skip
            return file_content

        # If it doesn't contain standard java type definitions, likely not worth documenting or it's a package-info / module-info
        # We can be deeper here, but for now let's just check for keywords
        if not any(k in file_content for k in ["class ", "interface ", "enum ", "record "]):
             return file_content

        result = self.agent.run_sync(file_content)
        content = result.output
        
        # Cleanup Markdown code blocks if present
        if content.startswith("```java"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
            
        if content.endswith("```"):
            content = content[:-3]
            
        return content.strip()
