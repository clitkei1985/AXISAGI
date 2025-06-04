import re
from typing import Dict
from enum import Enum

class TaskDomain(Enum):
    """Task domain categories for LLM selection"""
    CODE = "code"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    CONVERSATIONAL = "conversational"
    TECHNICAL = "technical"
    SCIENTIFIC = "scientific"
    EDUCATIONAL = "educational"
    BUSINESS = "business"
    TRANSLATION = "translation"
    AUDIO = "audio"
    IMAGE = "image"
    WEB_SEARCH = "web_search"
    REASONING = "reasoning"
    GENERAL = "general"

class DomainDetector:
    """Domain detection logic separated for modularity"""
    
    def __init__(self):
        # Domain detection patterns
        self.domain_patterns = {
            TaskDomain.CODE: [
                r'\b(function|class|def|import|export|const|var|let)\b',
                r'\b(python|javascript|typescript|java|c\+\+|rust|go)\b',
                r'```\w*\n',
                r'\b(debug|refactor|optimize|test)\b',
                r'\b(api|endpoint|database|sql)\b'
            ],
            TaskDomain.CREATIVE: [
                r'\b(write|story|poem|creative|imagine|describe)\b',
                r'\b(character|plot|narrative|scene)\b',
                r'\b(art|music|design|aesthetic)\b'
            ],
            TaskDomain.ANALYTICAL: [
                r'\b(analyze|compare|evaluate|assess|study)\b',
                r'\b(data|statistics|trends|patterns)\b',
                r'\b(research|findings|conclusions)\b'
            ],
            TaskDomain.TECHNICAL: [
                r'\b(configure|setup|install|deploy)\b',
                r'\b(system|network|server|infrastructure)\b',
                r'\b(performance|optimization|scaling)\b'
            ],
            TaskDomain.SCIENTIFIC: [
                r'\b(research|experiment|hypothesis|theory)\b',
                r'\b(physics|chemistry|biology|mathematics)\b',
                r'\b(formula|equation|calculation)\b'
            ],
            TaskDomain.EDUCATIONAL: [
                r'\b(explain|teach|learn|understand|tutorial)\b',
                r'\b(concept|principle|example|practice)\b',
                r'\b(student|homework|assignment)\b'
            ],
            TaskDomain.BUSINESS: [
                r'\b(strategy|market|business|finance|revenue)\b',
                r'\b(meeting|presentation|proposal|plan)\b',
                r'\b(customer|client|stakeholder)\b'
            ],
            TaskDomain.TRANSLATION: [
                r'\b(translate|translation|language)\b',
                r'\b(english|spanish|french|german|chinese|japanese)\b'
            ],
            TaskDomain.REASONING: [
                r'\b(logic|reasoning|argument|proof)\b',
                r'\b(because|therefore|however|although)\b',
                r'\b(cause|effect|reason|conclusion)\b'
            ]
        }
    
    def detect_task_domain(self, prompt: str, context: str = None) -> TaskDomain:
        """Detect the primary task domain from prompt content"""
        text = prompt.lower()
        if context:
            text += " " + context.lower()
        
        domain_scores = {}
        
        # Score each domain based on pattern matches
        for domain, patterns in self.domain_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches
            
            if score > 0:
                domain_scores[domain] = score
        
        # Return highest scoring domain or general if no clear match
        if domain_scores:
            return max(domain_scores.items(), key=lambda x: x[1])[0]
        
        return TaskDomain.GENERAL 