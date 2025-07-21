"""
AI-powered code generator with built-in validation
Combines OpenAI Code Interpreter with Knowledge Graph validation
"""

import asyncio
import openai
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

from knowledge_graph_validator import KnowledgeGraphValidator
from ai_script_analyzer import analyze_python_code

class ValidatedAICodeGenerator:
    """Generate code with AI and validate against knowledge graph"""
    
    def __init__(self, openai_api_key: str, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.validator = KnowledgeGraphValidator(neo4j_uri, neo4j_user, neo4j_password)
        self.max_iterations = 3  # Max refinement attempts
        
    async def initialize(self):
        """Initialize the validator"""
        await self.validator.initialize()
    
    async def close(self):
        """Clean up resources"""
        await self.validator.close()
    
    async def generate_validated_code(self, 
                                    prompt: str, 
                                    context_files: List[str] = None,
                                    requirements: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate code with AI and validate it against knowledge graph
        
        Args:
            prompt: Description of what code to generate
            context_files: Existing code files for context
            requirements: Additional requirements (imports, classes to use, etc.)
        """
        
        # Build enhanced prompt with knowledge graph context
        enhanced_prompt = await self._build_enhanced_prompt(prompt, context_files, requirements)
        
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            print(f"🤖 Generation attempt {iteration}...")
            
            # Generate code with OpenAI
            generated_code = await self._generate_code_with_openai(enhanced_prompt)
            
            # Validate the generated code
            validation_result = await self._validate_generated_code(generated_code)
            
            if not validation_result['hallucinations']:
                print(f"✅ Code generated successfully on attempt {iteration}")
                return {
                    'code': generated_code,
                    'validation': validation_result,
                    'attempts': iteration,
                    'status': 'success'
                }
            
            # If validation failed, provide feedback for refinement
            print(f"❌ Validation failed on attempt {iteration}")
            feedback = self._generate_feedback(validation_result)
            enhanced_prompt = self._refine_prompt_with_feedback(enhanced_prompt, feedback, generated_code)
        
        # Max attempts reached
        print(f"⚠️ Max attempts ({self.max_iterations}) reached")
        return {
            'code': generated_code,
            'validation': validation_result,
            'attempts': iteration,
            'status': 'max_attempts_reached'
        }
    
    async def _build_enhanced_prompt(self, 
                                   prompt: str, 
                                   context_files: List[str] = None,
                                   requirements: Dict[str, Any] = None) -> str:
        """Build an enhanced prompt with knowledge graph context"""
        
        enhanced_parts = [prompt]
        
        # Add context from existing files
        if context_files:
            enhanced_parts.append("\n## Available Context Files:")
            for file_path in context_files:
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        enhanced_parts.append(f"\n### {file_path}:\n```python\n{content}\n```")
                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}")
        
        # Add requirements
        if requirements:
            enhanced_parts.append("\n## Requirements:")
            if 'imports' in requirements:
                enhanced_parts.append(f"- Use these imports: {', '.join(requirements['imports'])}")
            if 'classes' in requirements:
                enhanced_parts.append(f"- Use these classes: {', '.join(requirements['classes'])}")
            if 'avoid' in requirements:
                enhanced_parts.append(f"- Avoid using: {', '.join(requirements['avoid'])}")
        
        # Add knowledge graph guidance
        enhanced_parts.append("""
## Code Generation Guidelines:
1. Only use imports and APIs that actually exist in the target codebase
2. Follow established patterns from the context files
3. Use proper parameter names and types as shown in examples
4. Prefer composition over complex inheritance
5. Include proper error handling
6. Add type hints where appropriate
""")
        
        return "\n".join(enhanced_parts)
    
    async def _generate_code_with_openai(self, prompt: str) -> str:
        """Generate code using OpenAI API"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert Python developer. Generate clean, well-documented Python code that follows best practices. Only use APIs and methods that exist in the provided context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for more deterministic code
                max_tokens=2000
            )
            
            generated_code = response.choices[0].message.content
            
            # Extract Python code from markdown if present
            if "```python" in generated_code:
                start = generated_code.find("```python") + 9
                end = generated_code.find("```", start)
                generated_code = generated_code[start:end].strip()
            
            return generated_code
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")
    
    async def _validate_generated_code(self, code: str) -> Dict[str, Any]:
        """Validate generated code against knowledge graph"""
        try:
            # Analyze the generated code
            analysis_result = await analyze_python_code(code)
            
            # Validate against knowledge graph
            validation_result = await self.validator.validate_script(analysis_result)
            
            return {
                'confidence': validation_result.overall_confidence,
                'hallucinations': validation_result.hallucinations_detected,
                'import_issues': [v for v in validation_result.import_validations 
                                if v.validation.status.value in ['INVALID', 'NOT_FOUND']],
                'method_issues': [v for v in validation_result.method_validations 
                                if v.validation.status.value in ['INVALID', 'NOT_FOUND']],
                'class_issues': [v for v in validation_result.class_validations 
                               if v.validation.status.value in ['INVALID', 'NOT_FOUND']]
            }
            
        except Exception as e:
            return {
                'confidence': 0.0,
                'hallucinations': [{'type': 'ANALYSIS_ERROR', 'description': str(e)}],
                'import_issues': [],
                'method_issues': [],
                'class_issues': []
            }
    
    def _generate_feedback(self, validation_result: Dict[str, Any]) -> str:
        """Generate feedback for code refinement"""
        feedback_parts = ["The generated code has the following issues that need to be fixed:"]
        
        for hallucination in validation_result['hallucinations']:
            if hallucination['type'] == 'METHOD_NOT_FOUND':
                feedback_parts.append(f"- {hallucination['description']}")
                if 'suggestion' in hallucination and hallucination['suggestion']:
                    feedback_parts.append(f"  Suggestion: Use {hallucination['suggestion']} instead")
            
            elif hallucination['type'] == 'ATTRIBUTE_NOT_FOUND':
                feedback_parts.append(f"- {hallucination['description']}")
            
            elif hallucination['type'] == 'INVALID_PARAMETERS':
                feedback_parts.append(f"- {hallucination['description']}")
        
        # Add specific issues
        if validation_result['import_issues']:
            feedback_parts.append("\nImport issues:")
            for issue in validation_result['import_issues']:
                feedback_parts.append(f"- Import '{issue.import_info.name}' not found")
        
        return "\n".join(feedback_parts)
    
    def _refine_prompt_with_feedback(self, original_prompt: str, feedback: str, failed_code: str) -> str:
        """Refine the prompt based on validation feedback"""
        return f"""
{original_prompt}

## Previous Attempt Failed
The following code was generated but failed validation:
```python
{failed_code}
```

## Issues Found:
{feedback}

## Instructions for Next Attempt:
1. Fix all the issues mentioned above
2. Only use methods and attributes that actually exist
3. Double-check parameter names and counts
4. Ensure all imports are valid and necessary
5. If unsure about an API, use simpler, more basic approaches

Please generate corrected code that addresses these specific issues.
"""

# Usage example
async def example_usage():
    """Example of using the validated AI code generator"""
    
    generator = ValidatedAICodeGenerator(
        openai_api_key="your-openai-key",
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password"
    )
    
    await generator.initialize()
    
    try:
        result = await generator.generate_validated_code(
            prompt="Create a function that processes user data using pydantic_ai Agent",
            context_files=["existing_agent.py", "data_models.py"],
            requirements={
                'imports': ['pydantic_ai'],
                'classes': ['Agent'],
                'avoid': ['deprecated_function']
            }
        )
        
        if result['status'] == 'success':
            print("Generated code:")
            print(result['code'])
            print(f"Validation confidence: {result['validation']['confidence']:.2f}")
        else:
            print(f"Generation failed: {result['status']}")
            print("Issues found:", result['validation']['hallucinations'])
            
    finally:
        await generator.close()

if __name__ == "__main__":
    asyncio.run(example_usage())