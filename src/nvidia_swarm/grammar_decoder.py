#!/usr/bin/env python3
"""
Grammar-Constrained Decoding Integration for NVIDIA Swarm
Based on: transformers-CFG (epfl-dlab/transformers-CFG)
Credit: https://github.com/epfl-dlab/transformers-CFG
License: MIT

This replaces our regex-based grammar with production EBNF grammar constraints
using IncrementalGrammarConstraint and GrammarConstrainedLogitsProcessor.
"""

import json, re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# EBNF grammar for JSON tool calls
TOOL_CALL_GRAMMAR = """
root ::= tool_call

tool_call ::= "{" \"tool\" ":" \"" tool_name \"" "," \"params\" ":" param_object "}"

tool_name ::= "web_search" | "web_open_url" | "ipython" | "write_file" | "get_data_source" | "nim_benchmark"

param_object ::= "{" pair ("," pair)* "}" | "{}"

pair ::= \"" key \"" ":" value

key ::= [a-zA-Z_][a-zA-Z0-9_]*

value ::= string | number | "true" | "false" | "null" | array | param_object

string ::= """ char* """

char ::= [a-zA-Z0-9_ ./:@?&=+-] | "\" escape

escape ::= """ | "\" | "/" | "b" | "f" | "n" | "r" | "t" | "u" [0-9a-fA-F]{4}

number ::= [0-9]+ ("." [0-9]+)?

array ::= "[" (value ("," value)*)? "]"
"""

@dataclass
class GrammarConfig:
    """Configuration for grammar-constrained decoding."""
    grammar_str: str
    root_rule: str = "root"
    tokenizer_name: str = "meta-llama/Llama-3.1-8B-Instruct"

    def to_ebnf(self) -> str:
        return self.grammar_str

class SwarmGrammarDecoder:
    """Production grammar-constrained decoder using EBNF.

    When transformers-cfg is installed, this uses IncrementalGrammarConstraint
    for true grammar-constrained decoding. Falls back to regex validation.
    """

    def __init__(self, grammar: Optional[GrammarConfig] = None):
        self.grammar = grammar or GrammarConfig(grammar_str=TOOL_CALL_GRAMMAR)
        self._has_transformers_cfg = False
        self._grammar_constraint = None
        self._logits_processor = None

        try:
            from transformers_cfg.grammar_utils import IncrementalGrammarConstraint
            from transformers_cfg.generation.logits_process import GrammarConstrainedLogitsProcessor
            from transformers import AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(self.grammar.tokenizer_name)
            self._grammar_constraint = IncrementalGrammarConstraint(
                self.grammar.grammar_str, 
                self.grammar.root_rule, 
                tokenizer
            )
            self._logits_processor = GrammarConstrainedLogitsProcessor(self._grammar_constraint)
            self._has_transformers_cfg = True
            print(f"[GCD] transformers-cfg loaded: {self.grammar.tokenizer_name}")
        except ImportError:
            print("[GCD] transformers-cfg not installed — using regex fallback")
        except Exception as e:
            print(f"[GCD] Error loading transformers-cfg: {e} — using regex fallback")

    def validate(self, text: str) -> bool:
        """Validate that text conforms to the grammar."""
        if self._has_transformers_cfg and self._grammar_constraint:
            try:
                # Test parse
                self._grammar_constraint._parse_string(text)
                return True
            except:
                return False
        else:
            # Regex fallback
            return self._regex_validate(text)

    def _regex_validate(self, text: str) -> bool:
        """Fallback regex validation for JSON tool calls."""
        pattern = r'\{\s*"tool"\s*:\s*"[a-zA-Z_]+"\s*,\s*"params"\s*:\s*\{[^}]*\}\s*\}'
        return bool(re.match(pattern, text.strip()))

    def get_logits_processor(self):
        """Get the logits processor for model.generate()."""
        return self._logits_processor

    def extract_tool_calls(self, text: str) -> List[Dict]:
        """Extract all tool calls from text."""
        tool_calls = []
        # Find JSON blocks
        for match in re.finditer(r'\{[^}]+"tool"[^}]+\}', text, re.DOTALL):
            try:
                tc = json.loads(match.group())
                if "tool" in tc and "params" in tc:
                    tool_calls.append(tc)
            except json.JSONDecodeError:
                pass
        return tool_calls

# === NVIDIA-NIM specific grammar for Llama 3.1 tool use ===
LLAMA_31_TOOL_GRAMMAR = """
root ::= tool_call | normal_response

tool_call ::= "{" ws \"tool\" ws ":" ws \"" tool_name \"" ws "," ws \"params\" ws ":" ws param_object ws "}"

tool_name ::= "web_search" | "web_open_url" | "ipython" | "write_file" | "get_data_source" | "spawn_agent" | "monitor_agents"

param_object ::= "{" ws (pair (ws "," ws pair)*)? ws "}"

pair ::= \"" key \"" ws ":" ws value

key ::= [a-zA-Z_][a-zA-Z0-9_]*

value ::= string | number | "true" | "false" | "null" | array | param_object

string ::= """ char* """

char ::= [a-zA-Z0-9_ ./:@?&=+\-] | "\" escape

escape ::= """ | "\" | "/" | "b" | "f" | "n" | "r" | "t" | "u" hexdigit{4}

hexdigit ::= [0-9a-fA-F]

number ::= [0-9]+ ("." [0-9]+)?

array ::= "[" ws (value (ws "," ws value)*)? ws "]"

ws ::= [ \t\n\r]*

normal_response ::= [^\{].*
"""

def create_swarm_decoder(tokenizer_name: str = "meta-llama/Llama-3.1-8B-Instruct") -> SwarmGrammarDecoder:
    """Create a grammar decoder optimized for swarm tool calls."""
    config = GrammarConfig(
        grammar_str=LLAMA_31_TOOL_GRAMMAR,
        root_rule="root",
        tokenizer_name=tokenizer_name,
    )
    return SwarmGrammarDecoder(config)

if __name__ == "__main__":
    decoder = create_swarm_decoder()

    # Test validation
    test_valid = '{"tool": "web_search", "params": {"query": "NVIDIA NIM"}}'
    test_invalid = '{"tool": "web_search", "params": {"query": "NVIDIA NIM"}'  # missing closing }

    print(f"Valid: {decoder.validate(test_valid)}")
    print(f"Invalid: {decoder.validate(test_invalid)}")

    # Test extraction
    text = 'I will search for that. {"tool": "web_search", "params": {"query": "test"}} Here are results.'
    calls = decoder.extract_tool_calls(text)
    print(f"Extracted: {calls}")
