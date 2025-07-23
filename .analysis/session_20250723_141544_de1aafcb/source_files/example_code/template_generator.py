"""
Template-based code generation with strict constraints
More deterministic than free-form generation
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from jinja2 import Template
import json

@dataclass
class CodeTemplate:
    """Represents a code template with constraints"""
    name: str
    template_str: str
    required_params: List[str]
    optional_params: List[str] = None
    validation_rules: Dict[str, Any] = None

class TemplateBasedGenerator:
    """Generate code using templates with AI parameter filling"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, CodeTemplate]:
        """Load predefined code templates"""
        templates = {}
        
        # API Client Template
        templates['api_client'] = CodeTemplate(
            name='api_client',
            template_str='''
"""
{{ description }}
"""
import asyncio
from typing import {{ type_hints }}
{% for import_item in imports %}
{{ import_item }}
{% endfor %}

class {{ class_name }}:
    """{{ class_description }}"""
    
    def __init__(self, {{ init_params }}):
        {% for param in init_assignments %}
        {{ param }}
        {% endfor %}
    
    {% for method in methods %}
    async def {{ method.name }}(self, {{ method.params }}) -> {{ method.return_type }}:
        """{{ method.description }}"""
        {% for line in method.body %}
        {{ line }}
        {% endfor %}
    {% endfor %}
''',
            required_params=['class_name', 'class_description', 'methods'],
            optional_params=['imports', 'init_params', 'init_assignments', 'type_hints'],
            validation_rules={
                'class_name': {'type': 'identifier', 'pattern': r'^[A-Z][a-zA-Z0-9_]*$'},
                'methods': {'type': 'list', 'min_length': 1}
            }
        )
        
        # Data Processing Template
        templates['data_processor'] = CodeTemplate(
            name='data_processor',
            template_str='''
"""
{{ description }}
"""
from typing import {{ type_hints }}
from pathlib import Path
import logging
{% for import_item in imports %}
{{ import_item }}
{% endfor %}

logger = logging.getLogger(__name__)

def {{ function_name }}({{ function_params }}) -> {{ return_type }}:
    """
    {{ function_description }}
    
    Args:
        {% for param in param_docs %}
        {{ param }}
        {% endfor %}
    
    Returns:
        {{ return_description }}
    """
    logger.info("Starting {{ function_name }}")
    
    try:
        {% for step in processing_steps %}
        # {{ step.comment }}
        {% for line in step.code %}
        {{ line }}
        {% endfor %}
        
        {% endfor %}
        
        logger.info("{{ function_name }} completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error in {{ function_name }}: {e}")
        raise
''',
            required_params=['function_name', 'function_description', 'processing_steps'],
            optional_params=['imports', 'function_params', 'return_type', 'param_docs']
        )
        
        # Agent Template
        templates['ai_agent'] = CodeTemplate(
            name='ai_agent',
            template_str='''
"""
{{ description }}
"""
from typing import {{ type_hints }}
import asyncio
{% for import_item in imports %}
{{ import_item }}
{% endfor %}

class {{ agent_name }}:
    """{{ agent_description }}"""
    
    def __init__(self, {{ init_params }}):
        {% for assignment in init_assignments %}
        {{ assignment }}
        {% endfor %}
        
        # Initialize agent
        self.agent = Agent(
            model={{ model }},
            {% for param, value in agent_params.items() %}
            {{ param }}={{ value }},
            {% endfor %}
        )
    
    {% for tool in tools %}
    @self.agent.tool
    async def {{ tool.name }}({{ tool.params }}) -> {{ tool.return_type }}:
        """{{ tool.description }}"""
        {% for line in tool.implementation %}
        {{ line }}
        {% endfor %}
    {% endfor %}
    
    async def {{ main_method_name }}(self, {{ main_method_params }}) -> {{ main_method_return }}:
        """{{ main_method_description }}"""
        try:
            result = await self.agent.run_async({{ main_method_input }})
            return {{ result_processing }}
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            raise
''',
            required_params=['agent_name', 'agent_description', 'main_method_name'],
            optional_params=['tools', 'model', 'agent_params', 'imports']
        )
        
        return templates
    
    def generate_with_ai_params(self, template_name: str, ai_prompt: str, 
                               fixed_params: Dict[str, Any] = None) -> str:
        """
        Generate code using template with AI-filled parameters
        
        This approach is more deterministic because:
        1. Structure is fixed by template
        2. AI only fills specific parameters
        3. Validation rules ensure correctness
        """
        
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = self.templates[template_name]
        
        # Get AI to extract parameters from prompt
        ai_params = self._extract_params_with_ai(ai_prompt, template)
        
        # Merge with fixed parameters
        if fixed_params:
            ai_params.update(fixed_params)
        
        # Validate parameters
        self._validate_params(ai_params, template)
        
        # Generate code
        jinja_template = Template(template.template_str)
        return jinja_template.render(**ai_params)
    
    def _extract_params_with_ai(self, prompt: str, template: CodeTemplate) -> Dict[str, Any]:
        """Use AI to extract structured parameters from natural language prompt"""
        
        # This would call OpenAI API with structured output
        extraction_prompt = f"""
        Extract the following parameters from this prompt: "{prompt}"
        
        Required parameters:
        {', '.join(template.required_params)}
        
        Optional parameters:
        {', '.join(template.optional_params or [])}
        
        Return as JSON with these exact keys. Be specific and concrete.
        For code sections, break them into logical steps.
        """
        
        # Placeholder - in real implementation, call OpenAI API
        # with structured output or function calling
        return self._mock_ai_extraction(prompt, template)
    
    def _mock_ai_extraction(self, prompt: str, template: CodeTemplate) -> Dict[str, Any]:
        """Mock AI parameter extraction (replace with real OpenAI call)"""
        
        # This is a simplified mock - real implementation would use OpenAI
        if 'agent' in prompt.lower():
            return {
                'agent_name': 'DataProcessingAgent',
                'agent_description': 'Agent for processing data requests',
                'main_method_name': 'process_request',
                'main_method_params': 'request: str',
                'main_method_return': 'str',
                'main_method_description': 'Process user request and return result',
                'main_method_input': 'request',
                'result_processing': 'result.data',
                'model': "'gpt-4'",
                'imports': ['from pydantic_ai import Agent'],
                'type_hints': 'Any, Dict, List',
                'init_params': 'model_name: str = "gpt-4"',
                'init_assignments': ['self.model_name = model_name'],
                'agent_params': {'system_prompt': '"You are a helpful assistant"'},
                'tools': []
            }
        
        elif 'api' in prompt.lower():
            return {
                'class_name': 'APIClient',
                'class_description': 'Client for API interactions',
                'description': 'API client implementation',
                'type_hints': 'Dict, List, Any',
                'imports': ['import httpx', 'import json'],
                'init_params': 'base_url: str, api_key: str',
                'init_assignments': ['self.base_url = base_url', 'self.api_key = api_key'],
                'methods': [
                    {
                        'name': 'get_data',
                        'params': 'endpoint: str',
                        'return_type': 'Dict[str, Any]',
                        'description': 'Fetch data from API endpoint',
                        'body': [
                            'async with httpx.AsyncClient() as client:',
                            '    response = await client.get(f"{self.base_url}/{endpoint}")',
                            '    return response.json()'
                        ]
                    }
                ]
            }
        
        return {}
    
    def _validate_params(self, params: Dict[str, Any], template: CodeTemplate):
        """Validate parameters against template rules"""
        
        # Check required parameters
        missing = set(template.required_params) - set(params.keys())
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")
        
        # Apply validation rules
        if template.validation_rules:
            for param, rules in template.validation_rules.items():
                if param in params:
                    self._validate_single_param(params[param], rules, param)
    
    def _validate_single_param(self, value: Any, rules: Dict[str, Any], param_name: str):
        """Validate a single parameter against its rules"""
        
        if 'type' in rules:
            if rules['type'] == 'identifier' and not isinstance(value, str):
                raise ValueError(f"Parameter {param_name} must be a string identifier")
            elif rules['type'] == 'list' and not isinstance(value, list):
                raise ValueError(f"Parameter {param_name} must be a list")
        
        if 'min_length' in rules and len(value) < rules['min_length']:
            raise ValueError(f"Parameter {param_name} must have at least {rules['min_length']} items")
        
        if 'pattern' in rules:
            import re
            if not re.match(rules['pattern'], str(value)):
                raise ValueError(f"Parameter {param_name} doesn't match required pattern")

# Usage example
def example_template_usage():
    """Example of template-based generation"""
    
    generator = TemplateBasedGenerator()
    
    # Generate an AI agent with natural language prompt
    prompt = "Create an agent that processes user data requests and validates them"
    
    code = generator.generate_with_ai_params(
        template_name='ai_agent',
        ai_prompt=prompt,
        fixed_params={
            'imports': ['from pydantic_ai import Agent', 'import logging'],
            'type_hints': 'Any, Dict, List, Optional'
        }
    )
    
    print("Generated code:")
    print(code)

if __name__ == "__main__":
    example_template_usage()