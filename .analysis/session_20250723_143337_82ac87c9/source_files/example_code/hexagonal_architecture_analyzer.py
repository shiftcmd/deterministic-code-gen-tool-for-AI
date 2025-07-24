#!/usr/bin/env python3
"""
Hexagonal Architecture Analyzer
Analyzes Python code to identify hexagonal architecture patterns and layers
"""

import ast
import re
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ArchitecturalTag:
    """Represents an architectural classification for a code element"""
    architectural_type: str
    layer: str
    hexagonal_role: str
    confidence: float
    is_interface: bool
    reasoning: str

class HexagonalArchitectureAnalyzer:
    """Analyzes code for hexagonal architecture patterns"""
    
    def __init__(self):
        self.domain_patterns = {
            'entity': ['entity', 'model', 'domain', 'aggregate', 'value_object'],
            'service': ['service', 'use_case', 'application', 'command', 'query'],
            'repository': ['repository', 'storage', 'persistence', 'dao'],
            'adapter': ['adapter', 'controller', 'handler', 'client', 'gateway'],
            'port': ['port', 'interface', 'protocol', 'contract'],
            'infrastructure': ['infrastructure', 'config', 'database', 'external']
        }
        
        self.layer_indicators = {
            'domain': ['domain', 'entity', 'model', 'aggregate', 'value_object', 'business'],
            'application': ['application', 'service', 'use_case', 'command', 'query', 'handler'],
            'infrastructure': ['infrastructure', 'adapter', 'repository', 'database', 'external', 'client'],
            'interface': ['interface', 'controller', 'api', 'web', 'rest', 'graphql']
        }
        
        self.interface_indicators = [
            'abc.ABC', 'Protocol', 'Interface', 'abstract', '@abstractmethod'
        ]

    def analyze_component_architecture(self, module_data: Dict) -> Dict:
        """Analyze a module's architectural characteristics"""
        
        # Create enhanced copy of module data
        analyzed_module = module_data.copy()
        
        # Analyze file-level architecture
        file_arch = self._analyze_file_architecture(module_data)
        analyzed_module['architectural_info'] = file_arch
        
        # Analyze classes with architectural tags
        if 'classes' in analyzed_module:
            analyzed_classes = []
            for cls in analyzed_module['classes']:
                arch_tags = self._analyze_class_architecture(cls, module_data)
                cls_with_arch = cls.copy()
                cls_with_arch['architectural_tags'] = arch_tags.__dict__
                analyzed_classes.append(cls_with_arch)
            analyzed_module['classes'] = analyzed_classes
        
        # Analyze functions with architectural context
        if 'functions' in analyzed_module:
            analyzed_functions = []
            for func in analyzed_module['functions']:
                arch_context = self._analyze_function_architecture(func, module_data)
                func_with_arch = func.copy()
                func_with_arch['architectural_context'] = arch_context
                analyzed_functions.append(func_with_arch)
            analyzed_module['functions'] = analyzed_functions
        
        return analyzed_module

    def _analyze_file_architecture(self, module_data: Dict) -> Dict:
        """Analyze file-level architectural characteristics"""
        
        file_path = module_data.get('path', '')
        file_name = module_data.get('name', '')
        
        # Analyze path structure
        path_parts = Path(file_path).parts
        layer_scores = {layer: 0 for layer in self.layer_indicators.keys()}
        
        # Score based on path components
        for part in path_parts:
            part_lower = part.lower()
            for layer, indicators in self.layer_indicators.items():
                for indicator in indicators:
                    if indicator in part_lower:
                        layer_scores[layer] += 1
        
        # Score based on filename
        file_lower = file_name.lower()
        for layer, indicators in self.layer_indicators.items():
            for indicator in indicators:
                if indicator in file_lower:
                    layer_scores[layer] += 2  # Filename gets higher weight
        
        # Determine dominant layer
        dominant_layer = max(layer_scores, key=layer_scores.get) if max(layer_scores.values()) > 0 else 'unknown'
        
        # Analyze architectural types present
        arch_types = []
        for arch_type, patterns in self.domain_patterns.items():
            for pattern in patterns:
                if pattern in file_lower or any(pattern in part.lower() for part in path_parts):
                    arch_types.append(arch_type)
        
        # Check if mixed layer (multiple high scores)
        high_scores = [layer for layer, score in layer_scores.items() if score > 0]
        is_mixed_layer = len(high_scores) > 1
        
        return {
            'dominant_layer': dominant_layer,
            'layer_scores': layer_scores,
            'architectural_types': arch_types,
            'is_mixed_layer': is_mixed_layer,
            'confidence': max(layer_scores.values()) / 5.0 if max(layer_scores.values()) > 0 else 0.1
        }

    def _analyze_class_architecture(self, class_data: Dict, module_data: Dict) -> ArchitecturalTag:
        """Analyze a class's architectural role"""
        
        class_name = class_data.get('name', '')
        class_name_lower = class_name.lower()
        
        # Check for interface indicators
        is_interface = self._is_interface_class(class_data)
        
        # Score architectural types
        arch_scores = {arch_type: 0 for arch_type in self.domain_patterns.keys()}
        
        # Score based on class name
        for arch_type, patterns in self.domain_patterns.items():
            for pattern in patterns:
                if pattern in class_name_lower:
                    arch_scores[arch_type] += 3
        
        # Score based on methods
        methods = class_data.get('methods', [])
        for method in methods:
            method_name = method.get('name', '').lower()
            for arch_type, patterns in self.domain_patterns.items():
                for pattern in patterns:
                    if pattern in method_name:
                        arch_scores[arch_type] += 1
        
        # Score based on inheritance
        bases = class_data.get('bases', [])
        for base in bases:
            base_lower = base.lower()
            for arch_type, patterns in self.domain_patterns.items():
                for pattern in patterns:
                    if pattern in base_lower:
                        arch_scores[arch_type] += 2
        
        # Determine architectural type
        arch_type = max(arch_scores, key=arch_scores.get) if max(arch_scores.values()) > 0 else 'unknown'
        
        # Determine layer based on architectural type
        layer = self._determine_layer_from_arch_type(arch_type)
        
        # Determine hexagonal role
        hex_role = self._determine_hexagonal_role(arch_type, is_interface)
        
        # Calculate confidence
        max_score = max(arch_scores.values())
        confidence = min(max_score / 5.0, 1.0) if max_score > 0 else 0.1
        
        # Generate reasoning
        reasoning = self._generate_reasoning(class_name, arch_type, layer, hex_role, max_score)
        
        return ArchitecturalTag(
            architectural_type=arch_type,
            layer=layer,
            hexagonal_role=hex_role,
            confidence=confidence,
            is_interface=is_interface,
            reasoning=reasoning
        )

    def _analyze_function_architecture(self, function_data: Dict, module_data: Dict) -> Dict:
        """Analyze a function's architectural context"""
        
        func_name = function_data.get('name', '').lower()
        
        # Score architectural context
        context_scores = {arch_type: 0 for arch_type in self.domain_patterns.keys()}
        
        for arch_type, patterns in self.domain_patterns.items():
            for pattern in patterns:
                if pattern in func_name:
                    context_scores[arch_type] += 2
        
        # Determine primary context
        primary_context = max(context_scores, key=context_scores.get) if max(context_scores.values()) > 0 else 'utility'
        
        return {
            'primary_context': primary_context,
            'context_scores': context_scores,
            'confidence': max(context_scores.values()) / 3.0 if max(context_scores.values()) > 0 else 0.1
        }

    def _is_interface_class(self, class_data: Dict) -> bool:
        """Check if a class is an interface/abstract class"""
        
        # Check bases for ABC or Protocol
        bases = class_data.get('bases', [])
        for base in bases:
            if any(indicator in base for indicator in ['ABC', 'Protocol', 'Interface']):
                return True
        
        # Check for abstract methods
        methods = class_data.get('methods', [])
        for method in methods:
            if method.get('is_abstract', False):
                return True
        
        # Check class name patterns
        class_name = class_data.get('name', '')
        if class_name.startswith('I') and class_name[1:2].isupper():  # Interface naming convention
            return True
        
        if any(pattern in class_name.lower() for pattern in ['interface', 'protocol', 'contract']):
            return True
        
        return False

    def _determine_layer_from_arch_type(self, arch_type: str) -> str:
        """Determine layer based on architectural type"""
        
        layer_mapping = {
            'entity': 'domain',
            'service': 'application',
            'repository': 'infrastructure',
            'adapter': 'infrastructure',
            'port': 'interface',
            'infrastructure': 'infrastructure'
        }
        
        return layer_mapping.get(arch_type, 'unknown')

    def _determine_hexagonal_role(self, arch_type: str, is_interface: bool) -> str:
        """Determine hexagonal architecture role"""
        
        if is_interface:
            return 'port'
        
        role_mapping = {
            'entity': 'domain_core',
            'service': 'application_core',
            'repository': 'secondary_adapter',
            'adapter': 'primary_adapter',
            'port': 'port',
            'infrastructure': 'infrastructure'
        }
        
        return role_mapping.get(arch_type, 'unknown')

    def _generate_reasoning(self, class_name: str, arch_type: str, layer: str, hex_role: str, score: int) -> str:
        """Generate human-readable reasoning for the classification"""
        
        reasoning_parts = []
        
        reasoning_parts.append(f"Class '{class_name}' classified as {arch_type}")
        reasoning_parts.append(f"assigned to {layer} layer")
        reasoning_parts.append(f"with hexagonal role: {hex_role}")
        reasoning_parts.append(f"(confidence score: {score})")
        
        return "; ".join(reasoning_parts)

    def get_architecture_summary(self, analyzed_modules: List[Dict]) -> Dict:
        """Generate summary of architectural analysis"""
        
        layer_counts = {}
        arch_type_counts = {}
        hex_role_counts = {}
        
        for module in analyzed_modules:
            # Count file-level architecture
            file_arch = module.get('architectural_info', {})
            layer = file_arch.get('dominant_layer', 'unknown')
            layer_counts[layer] = layer_counts.get(layer, 0) + 1
            
            # Count class-level architecture
            for cls in module.get('classes', []):
                arch_tags = cls.get('architectural_tags', {})
                arch_type = arch_tags.get('architectural_type', 'unknown')
                hex_role = arch_tags.get('hexagonal_role', 'unknown')
                
                arch_type_counts[arch_type] = arch_type_counts.get(arch_type, 0) + 1
                hex_role_counts[hex_role] = hex_role_counts.get(hex_role, 0) + 1
        
        return {
            'layer_distribution': layer_counts,
            'architectural_type_distribution': arch_type_counts,
            'hexagonal_role_distribution': hex_role_counts,
            'total_modules_analyzed': len(analyzed_modules)
        }
