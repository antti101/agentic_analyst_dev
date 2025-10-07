# semantic_layer_mcp.py - Core Semantic Layer Parser and MCP Server

import asyncio
import json
import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from .log_manager import logger
from .config_loader import config
from autogen import ConversableAgent, UserProxyAgent

# Monkey patch for capturing OpenAI client usage
original_openai_create = None

@dataclass
class SemanticItem:
    """Represents a semantic layer item (measure or dimension)"""
    name: str
    group: str  # 'measures' or 'dimensions'
    cube_name: str
    variants: str
    hint: str
    
    @property
    def item_name(self) -> str:
        """Get the item name without cube prefix"""
        if '.' in self.name:
            return self.name.split('.', 1)[1]
        return self.name
    
    @property
    def has_variants(self) -> bool:
        """Check if item has predefined variants"""
        return self.variants != "None" and self.variants != ""

class SemanticLayerParser:
    """Parser for semantic layer JSONL file"""
    
    def __init__(self, file_path: str):
        self.file_path = os.path.expanduser(file_path)
        self.items: List[SemanticItem] = []
        self.cubes: Set[str] = set()
        self._load_semantic_layer()
    
    def _load_semantic_layer(self):
        """Load semantic layer from JSONL file"""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Semantic layer file not found: {self.file_path}")
        
        self.items = []
        self.cubes = set()
        
        with open(self.file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        item = SemanticItem(
                            name=data.get('name', ''),
                            group=data.get('group', ''),
                            cube_name=data.get('cube_name', ''),
                            variants=data.get('variants', 'None'),
                            hint=data.get('hint', '')
                        )
                        self.items.append(item)
                        self.cubes.add(item.cube_name)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing line: {line}, Error: {e}")
        
        print(f"Loaded {len(self.items)} semantic items across {len(self.cubes)} cubes")

class DataPlatformSemanticServer:
    """Semantic Layer Server for Data Platform"""
    
    def __init__(self, semantic_layer_path: str):
        self.parser = SemanticLayerParser(semantic_layer_path)
    
    def search_semantic_items(self, query: str, cube_name: Optional[str] = None, 
                            item_type: Optional[str] = None) -> List[Dict]:
        """Search semantic items by name, hint, or cube"""
        results = []
        query_lower = query.lower()
        
        for item in self.parser.items:
            if cube_name and item.cube_name.lower() != cube_name.lower():
                continue
            if item_type and item.group.lower() != item_type.lower():
                continue
            if (query_lower in item.name.lower() or 
                query_lower in item.hint.lower() or 
                query_lower in item.cube_name.lower()):
                results.append({
                    'name': item.name, 'item_name': item.item_name, 'group': item.group,
                    'cube_name': item.cube_name, 'variants': item.variants if item.has_variants else None,
                    'hint': item.hint, 'has_variants': item.has_variants
                })
        return results
    
    def get_cubes(self) -> List[Dict[str, Any]]:
        """Get all available cubes (data marts) with their metrics"""
        cube_info = defaultdict(lambda: {'measures': 0, 'dimensions': 0, 'items': []})
        for item in self.parser.items:
            cube_info[item.cube_name][item.group] += 1
            cube_info[item.cube_name]['items'].append({
                'name': item.name, 'item_name': item.item_name, 'group': item.group,
                'has_hint': bool(item.hint.strip()), 'has_variants': item.has_variants
            })
        result = []
        for cube_name, info in cube_info.items():
            result.append({
                'cube_name': cube_name, 'total_items': info['measures'] + info['dimensions'],
                'measures_count': info['measures'], 'dimensions_count': info['dimensions'],
                'sample_items': info['items'][:5]
            })
        return sorted(result, key=lambda x: x['total_items'], reverse=True)
    
    def get_cube_details(self, cube_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific cube"""
        cube_items = [item for item in self.parser.items if item.cube_name.lower() == cube_name.lower()]
        if not cube_items:
            return None
        measures = []
        dimensions = []
        for item in cube_items:
            item_data = {
                'name': item.name, 'item_name': item.item_name, 'hint': item.hint,
                'variants': item.variants if item.has_variants else None, 'has_variants': item.has_variants
            }
            if item.group == 'measures':
                measures.append(item_data)
            else:
                dimensions.append(item_data)
        return {
            'cube_name': cube_name, 'total_items': len(cube_items),
            'measures': {'count': len(measures), 'items': measures},
            'dimensions': {'count': len(dimensions), 'items': dimensions}
        }
    
    def get_measures(self, cube_name: Optional[str] = None) -> List[Dict]:
        """Get all measures, optionally filtered by cube"""
        measures = [item for item in self.parser.items if item.group == 'measures']
        if cube_name:
            measures = [m for m in measures if m.cube_name.lower() == cube_name.lower()]
        return [{'name': m.name, 'item_name': m.item_name, 'cube_name': m.cube_name, 'hint': m.hint,
                 'variants': m.variants if m.has_variants else None} for m in measures]
    
    def get_dimensions(self, cube_name: Optional[str] = None) -> List[Dict]:
        """Get all dimensions, optionally filtered by cube"""
        dimensions = [item for item in self.parser.items if item.group == 'dimensions']
        if cube_name:
            dimensions = [d for d in dimensions if d.cube_name.lower() == cube_name.lower()]
        return [{'name': d.name, 'item_name': d.item_name, 'cube_name': d.cube_name, 'hint': d.hint,
                 'variants': d.variants if d.has_variants else None, 'has_variants': d.has_variants} for d in dimensions]

class BIAnalystAgent:
    """Single BI Analyst agent that interfaces with semantic layer"""
    
    def __init__(self, semantic_server: DataPlatformSemanticServer, llm_config: dict):
        self.semantic_server = semantic_server
        self.llm_config = llm_config

        self._setup_agent()
    
    def _setup_agent(self):
        """Setup single BI Analyst agent with comprehensive semantic layer tools"""
        self.user_proxy = UserProxyAgent(
           name="user_proxy", human_input_mode="NEVER", max_consecutive_auto_reply=0,
           llm_config=False, default_auto_reply="", system_message="A proxy for the user."
        )
        with open("prompts/bi_analyst_prompt.txt", "r") as f:
            system_message = f.read()

        is_silent = config.get("autogen.bi_analyst.agent_silent", True)
        print(f"DEBUG: Initializing agent with silent={is_silent}")

        # Enhance LLM config with usage tracking
        enhanced_llm_config = self.llm_config.copy()
        enhanced_llm_config["config_list"] = self._add_usage_tracking_to_config(
            enhanced_llm_config.get("config_list", [enhanced_llm_config])
        )

        self.bi_analyst = ConversableAgent(
            name="BIAnalyst",
            system_message=system_message,
            llm_config=enhanced_llm_config, human_input_mode="NEVER", silent=is_silent
        )
        self._register_semantic_tools()

    def _add_usage_tracking_to_config(self, config_list):
        """Add usage tracking wrapper to LLM config"""
        enhanced_configs = []
        for config in config_list:
            enhanced_config = config.copy()
            # Don't add empty functions array - this causes OpenAI API errors
            # The tools are registered separately via register_for_execution
            enhanced_configs.append(enhanced_config)
        return enhanced_configs
    
    def _register_semantic_tools(self):
        """Register all semantic layer methods as AutoGen tools for the BI Analyst"""
        @self.bi_analyst.register_for_execution()
        def search_semantic_items(query: str, cube_name: str = None, item_type: str = None) -> str:
            return json.dumps(self.semantic_server.search_semantic_items(query, cube_name, item_type), indent=2)
        
        @self.bi_analyst.register_for_execution()
        def get_cubes() -> str:
            return json.dumps(self.semantic_server.get_cubes(), indent=2)
        
        @self.bi_analyst.register_for_execution()
        def get_cube_details(cube_name: str) -> str:
            result = self.semantic_server.get_cube_details(cube_name)
            if result:
                return json.dumps(result, indent=2)
            return f"Cube '{cube_name}' not found."
        
        @self.bi_analyst.register_for_execution()
        def get_measures(cube_name: str = None) -> str:
            return json.dumps(self.semantic_server.get_measures(cube_name), indent=2)
        
        @self.bi_analyst.register_for_execution()
        def get_dimensions(cube_name: str = None) -> str:
            return json.dumps(self.semantic_server.get_dimensions(cube_name), indent=2)

    def run_generate_agent_reply(self, messages: list):
        """Sync wrapper to run the async reply generation."""
        return asyncio.run(self.generate_agent_reply(messages))

    async def generate_agent_reply(self, messages: list):
        """Generate a reply, logging the internal agent planning and token usage."""
        logger.info("Agent reply generation started.", extra={"event": "generate_reply_start"})

        history = self.bi_analyst.chat_messages.get(self.user_proxy, [])
        messages_before = len(history)

        # Hook into the LLM config to track usage at the source
        original_llm_config = self.bi_analyst.llm_config.copy()

        # Create a wrapper function to capture usage
        def usage_tracking_wrapper(original_client):
            class UsageTrackingClient:
                def __init__(self, client):
                    self._client = client

                def __getattr__(self, name):
                    attr = getattr(self._client, name)
                    if name == 'create' and hasattr(attr, '__call__'):
                        def create_wrapper(*args, **kwargs):
                            result = attr(*args, **kwargs)
                            # Log usage if available in the result
                            if hasattr(result, 'usage') and result.usage:
                                logger.info("LLM call completed", extra={
                                    "event": "token_usage",
                                    "details": {
                                        "prompt_tokens": result.usage.prompt_tokens,
                                        "completion_tokens": result.usage.completion_tokens,
                                        "total_tokens": result.usage.total_tokens
                                    }
                                })
                            return result
                        return create_wrapper
                    return attr
            return UsageTrackingClient(original_client)

        reply = self.bi_analyst.generate_reply(messages=messages, sender=self.user_proxy)
        if asyncio.iscoroutine(reply):
            final_reply = await reply
        else:
            final_reply = reply

        messages_after = self.bi_analyst.chat_messages.get(self.user_proxy, [])
        new_messages = messages_after[messages_before:]

        # Debug: Log the structure of new messages to understand AutoGen's format
        for i, msg in enumerate(new_messages):
            logger.info("Message structure debug", extra={
                "event": "message_debug",
                "message_index": i,
                "message_keys": list(msg.keys()),
                "message_content": str(msg)[:500]  # First 500 chars to avoid huge logs
            })

            if msg.get("tool_calls"):
                logger.info("Agent planning to use tools", extra={"event": "tool_call", "details": msg["tool_calls"]})

            # Enhanced usage extraction with multiple possible locations
            usage = None
            usage_locations = []

            # Check direct usage field
            if msg.get("usage"):
                usage = msg.get("usage")
                usage_locations.append("direct_usage")

            # Check metadata.usage
            if msg.get("metadata") and isinstance(msg.get("metadata"), dict) and msg["metadata"].get("usage"):
                usage = msg["metadata"].get("usage")
                usage_locations.append("metadata_usage")

            # Check for response.usage (common in OpenAI responses)
            if msg.get("response") and isinstance(msg.get("response"), dict) and msg["response"].get("usage"):
                usage = msg["response"].get("usage")
                usage_locations.append("response_usage")

            # Check for cost information (AutoGen sometimes tracks this)
            if msg.get("cost"):
                logger.info("Cost information found", extra={"event": "cost_tracking", "details": msg["cost"]})

            # Log usage if found
            if usage:
                logger.info("LLM call completed", extra={
                    "event": "token_usage",
                    "details": usage,
                    "usage_source": usage_locations
                })
            else:
                # Log that no usage was found for debugging
                logger.info("No usage data found in message", extra={
                    "event": "usage_not_found",
                    "available_keys": list(msg.keys())
                })

        return final_reply

class DataPlatformApp:
    """Base class for the Data Platform application, responsible for the semantic server."""
    
    def __init__(self, semantic_layer_path: str):
        self.semantic_server = DataPlatformSemanticServer(semantic_layer_path)

def demo_system():
    print("Demo system is for testing the semantic layer directly.")

if __name__ == "__main__":
    demo_system()
