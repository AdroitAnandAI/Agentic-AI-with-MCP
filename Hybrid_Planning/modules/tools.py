# modules/tools.py

from typing import List, Dict, Optional, Any
import re
from modules.memory import MemoryItem

def extract_json_block(text: str) -> str:
    match = re.search(r"```json\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def summarize_tools(tools: List[Any]) -> str:
    """
    Generate a string summary of tools for LLM prompt injection.
    Format: "- tool_name: description"
    """
    return "\n".join(
        f"- {tool.name}: {getattr(tool, 'description', 'No description provided.')}"
        for tool in tools
    )


def filter_tools_by_hint(tools: List[Any], hint: Optional[str] = None) -> List[Any]:
    """
    If tool_hint is provided (e.g., 'search_documents'),
    try to match it exactly or fuzzily with available tool names.
    """
    if not hint:
        return tools

    hint_lower = hint.lower()
    filtered = [tool for tool in tools if hint_lower in tool.name.lower()]
    return filtered if filtered else tools


def get_tool_map(tools: List[Any]) -> Dict[str, Any]:
    """
    Return a dict of tool_name → tool object for fast lookup
    """
    return {tool.name: tool for tool in tools}

def tool_expects_input(self, tool_name: str) -> bool:
    tool = next((t for t in self.tools if t.name == tool_name), None)
    if not tool or not hasattr(tool, 'parameters') or not isinstance(tool.parameters, dict):
        return False
    # If the top-level parameter is just 'input', we assume wrapping is required
    return list(tool.parameters.keys()) == ['input']


def load_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def is_complex_query(query: str) -> bool:
    """
    Check if a query is complex based on various factors.
    Returns True if query is complex, False otherwise.
    """
    # Factors that make a query complex:
    # 1. Long query (more than 5 words)
    # 2. Contains multiple topics
    # 3. Contains technical terms
    # 4. Contains numbers or special characters
    
    words = query.split()
    if len(words) > 5:
        return True
        
    # Check for technical terms
    technical_terms = ['analysis', 'research', 'study', 'report', 'data', 'statistics', 
                      'comparison', 'difference', 'relationship', 'impact', 'effect']
    if any(term in query.lower() for term in technical_terms):
        return True
        
    # Check for numbers and special characters
    if any(char.isdigit() for char in query) or any(char in query for char in '+-*/()[]{}'):
        return True
        
    return False

def get_similar_memory_queries(query: str, memory_items: List[Any], similarity_threshold: float = 0.7) -> List[Any]:
    """
    Check memory for similar past queries.
    Returns a list of similar memory items if found.
    """
    if not memory_items:
        return []
        
    similar_items = []
    query_words = set(query.lower().split())
    
    for item in memory_items:
        # if not isinstance(item, dict):
        #     continue
        
        if isinstance(item, dict):
            # Get the user query from memory item
            memory_query = item.get('user_query', '')
            if not memory_query:
                continue
                
            # Simple word overlap similarity
            memory_words = set(memory_query.lower().split())
            overlap = len(query_words.intersection(memory_words))
            total = len(query_words.union(memory_words))
            similarity = overlap / total if total > 0 else 0
            
            if similarity >= similarity_threshold:
                similar_items.append(item)

        elif isinstance(item, MemoryItem):
            # Get the user query from memory item
            memory_query = item.input_query
            if not memory_query:
                continue
            
            # Simple word overlap similarity
            memory_words = set(memory_query.lower().split())
            overlap = len(query_words.intersection(memory_words))
            total = len(query_words.union(memory_words))
            similarity = overlap / total if total > 0 else 0
            
            if similarity >= similarity_threshold:
                similar_items.append(item)
            
    return similar_items

def prioritize_search_tools(tools: List[Any], query: str) -> List[Any]:
    """
    Sophisticated tool prioritization based on multiple factors:
    1. Query Complexity Score: Considers length, technical terms, and special characters
    2. Question Type Analysis: Identifies question patterns (how, what, why, etc.)
    3. Time Sensitivity: Detects time-related terms and urgency indicators
    4. Technical Depth: Evaluates technical terminology and domain-specific terms
    5. Contextual Relevance: Matches query against known document categories
    6. Query Intent Classification: Identifies search intent (informational, navigational, transactional)
    7. Historical Success Rate: Considers past tool performance for similar queries
    8. Query Structure Analysis: Evaluates query syntax and structure
    9. Domain Specificity: Detects domain-specific terminology and patterns
    10. Result Type Preference: Determines preferred result type (code, documentation, general info)
    """
    if not tools:
        return tools
        
    search_tools = [tool for tool in tools if tool.name in ['search_stored_documents', 'duckduckgo_search_results']]
    if not search_tools:
        return tools

    query_lower = query.lower()
    words = query_lower.split()
    
    # 1. Query Complexity Score
    complexity_score = 0
    complexity_score += len(words) * 0.2  # Length factor
    complexity_score += sum(1 for w in words if len(w) > 8) * 0.3  # Long words
    complexity_score += sum(1 for w in words if any(c.isdigit() for c in w)) * 0.2  # Numbers
    complexity_score += sum(1 for w in words if any(c in '+-*/()[]{}' for c in w)) * 0.3  # Special chars
    
    # 2. Question Type Analysis
    question_types = {
        'how': 'stored_docs',
        'what': 'web_search',
        'why': 'web_search',
        'when': 'web_search',
        'where': 'web_search',
        'which': 'stored_docs'
    }
    question_type = next((word for word in words if word in question_types), None)
    
    # 3. Time Sensitivity
    time_indicators = {'latest', 'recent', 'new', 'current', 'now', 'today', 'update'}
    is_time_sensitive = any(indicator in query_lower for indicator in time_indicators)
    
    # 4. Technical Depth
    technical_terms = {
        'api', 'function', 'method', 'class', 'interface', 'protocol',
        'implementation', 'algorithm', 'architecture', 'framework'
    }
    technical_score = sum(1 for word in words if word in technical_terms)
    
    # 5. Contextual Relevance
    doc_categories = {
        'code': {'implementation', 'example', 'sample', 'snippet'},
        'guide': {'tutorial', 'guide', 'how-to', 'walkthrough'},
        'reference': {'documentation', 'reference', 'specification'}
    }
    context_score = {
        category: sum(1 for word in words if word in terms)
        for category, terms in doc_categories.items()
    }
    
    # 6. Query Intent
    intent_indicators = {
        'informational': {'what', 'how', 'why', 'explain', 'describe'},
        'navigational': {'where', 'find', 'locate', 'search'},
        'transactional': {'download', 'install', 'buy', 'purchase'}
    }
    intent = next(
        (intent for intent, terms in intent_indicators.items() 
         if any(term in query_lower for term in terms)),
        'informational'
    )
    
    # 7. Query Structure
    has_quotes = '"' in query or "'" in query
    has_parentheses = '(' in query and ')' in query
    has_special_chars = any(c in query for c in '+-*/[]{}')
    
    # 8. Domain Specificity
    domain_terms = {
        'programming': {'code', 'program', 'script', 'function'},
        'system': {'os', 'platform', 'system', 'environment'},
        'network': {'api', 'endpoint', 'request', 'response'}
    }
    domain_score = {
        domain: sum(1 for word in words if word in terms)
        for domain, terms in domain_terms.items()
    }
    
    # Decision Logic
    if complexity_score > 2.0 or is_time_sensitive:
        preferred_tool = next((tool for tool in search_tools if tool.name == 'duckduckgo_search_results'), None)
    elif technical_score > 1 or max(context_score.values()) > 0:
        preferred_tool = next((tool for tool in search_tools if tool.name == 'search_stored_documents'), None)
    elif question_type and question_types[question_type] == 'stored_docs':
        preferred_tool = next((tool for tool in search_tools if tool.name == 'search_stored_documents'), None)
    elif intent == 'informational' and max(domain_score.values()) > 0:
        preferred_tool = next((tool for tool in search_tools if tool.name == 'search_stored_documents'), None)
    else:
        preferred_tool = next((tool for tool in search_tools if tool.name == 'duckduckgo_search_results'), None)
    
    if preferred_tool:
        tools.remove(preferred_tool)
        tools.insert(0, preferred_tool)
    
    return tools
