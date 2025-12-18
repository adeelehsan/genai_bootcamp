"""
Customer Support Chatbot with GROQ LLM Integration
"""

import json
from groq import Groq
from mcp_client import MCPClient
from config import GROQ_API_KEY, GROQ_MODEL, CATEGORIES


class CustomerSupportBot:
    """Chatbot that uses GROQ LLM to understand intent and MCP for data."""

    def __init__(self):
        self.groq = Groq(api_key=GROQ_API_KEY)
        self.mcp = MCPClient()
        self.session = {
            "authenticated": False,
            "customer_id": None,
            "customer_name": None,
            "email": None
        }

    def _get_tools(self):
        """Define tools available to the LLM."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_products",
                    "description": "List products by category. Pass the category parameter.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "The product category to list",
                                "enum": ["Computers", "Monitors", "Printers", "Accessories", "Networking"]
                            }
                        },
                        "required": ["category"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_products",
                    "description": "Search products by keyword.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search keyword"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_product",
                    "description": "Get detailed info about a specific product by SKU.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sku": {
                                "type": "string",
                                "description": "Product SKU (e.g., 'COM-0001', 'MON-0051')"
                            }
                        },
                        "required": ["sku"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "verify_customer",
                    "description": "Verify customer identity with email and PIN. Use when user wants to check orders or needs authentication.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "Customer email address"
                            },
                            "pin": {
                                "type": "string",
                                "description": "4-digit PIN code"
                            }
                        },
                        "required": ["email", "pin"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_orders",
                    "description": "List customer orders. Requires authentication first. Call with no parameters to get all orders, or filter by status: draft, submitted, approved, fulfilled, cancelled.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_order",
                    "description": "Get details of a specific order by ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "Order ID (UUID format)"
                            }
                        },
                        "required": ["order_id"]
                    }
                }
            }
        ]

    def _execute_tool(self, tool_name: str, args: dict) -> str:
        """Execute a tool and return the result."""
        try:
            if tool_name == "list_products":
                return self.mcp.list_products(category=args["category"])

            elif tool_name == "search_products":
                return self.mcp.search_products(args["query"])

            elif tool_name == "get_product":
                return self.mcp.get_product(args["sku"])

            elif tool_name == "verify_customer":
                result = self.mcp.verify_customer_pin(args["email"], args["pin"])
                if "Customer:" in result:
                    # Extract customer info from result
                    self.session["authenticated"] = True
                    self.session["email"] = args["email"]
                    # Parse customer ID from result (simplified)
                    lines = result.split("\n")
                    for line in lines:
                        if "ID:" in line:
                            self.session["customer_id"] = line.split("ID:")[1].strip()
                        if "Name:" in line:
                            self.session["customer_name"] = line.split("Name:")[1].strip()
                return result

            elif tool_name == "list_orders":
                if not self.session["authenticated"]:
                    return "Please verify your identity first. I'll need your email and PIN."
                return self.mcp.list_orders(customer_id=self.session["customer_id"])

            elif tool_name == "get_order":
                return self.mcp.get_order(args["order_id"])

            else:
                return f"Unknown tool: {tool_name}"

        except Exception as e:
            return f"Error: {str(e)}"

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the chatbot."""
        auth_status = ""
        if self.session["authenticated"]:
            auth_status = f"\n\nCurrent user: {self.session['customer_name']} (authenticated)"
        else:
            auth_status = "\n\nUser is not authenticated. Ask for email and PIN if they want to check orders."

        return f"""You are a customer support assistant for a computer products company.

RULES:
1. When user asks to see products, ALWAYS use the list_products or search_products tool.
2. Display the tool results to the user.
3. Never make up product information.

Available categories: Computers, Monitors, Printers, Accessories, Networking
{auth_status}"""

    def _clean_response(self, text: str) -> str:
        """Remove any function call notation from response."""
        import re
        # Remove patterns like (function=name>{"args"}<function) or similar
        text = re.sub(r'\(function[^)]*\)', '', text)
        text = re.sub(r'<function>', '', text)
        text = re.sub(r'<function', '', text)
        text = re.sub(r'function>', '', text)
        return text.strip()

    def _get_result_limit(self, message: str) -> int:
        """Extract the number of results user wants, or 0 for all."""
        import re
        message_lower = message.lower()

        # Patterns like "top 10", "first 5", "best 3", "show 10", "give me 5"
        patterns = [
            r'\btop\s+(\d+)',
            r'\bfirst\s+(\d+)',
            r'\bbest\s+(\d+)',
            r'\bshow\s+(\d+)',
            r'\bgive\s+me\s+(\d+)',
            r'\b(\d+)\s+products?\b',
            r'\b(\d+)\s+monitors?\b',
            r'\b(\d+)\s+computers?\b',
            r'\b(\d+)\s+printers?\b',
            r'\b(\d+)\s+accessories\b',
        ]

        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                return int(match.group(1))
        return 0  # 0 means show all

    def _limit_product_results(self, result: str, limit: int) -> str:
        """Limit product results to specified number and format as list."""
        import re

        lines = result.split('\n')
        output_lines = []
        product_count = 0
        total_products = 0

        # First pass: count total products
        for line in lines:
            if line.strip().startswith('[') and ']' in line:
                total_products += 1

        # Second pass: format output
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Check if this is a product line (starts with [SKU])
            if stripped.startswith('[') and ']' in stripped:
                product_count += 1
                if limit <= 0 or product_count <= limit:
                    # Format as numbered list item
                    output_lines.append(f"{product_count}. {stripped}")

        # Create header
        if limit > 0 and limit < total_products:
            header = f"Showing top {limit} of {total_products} products:\n"
        else:
            header = f"Found {total_products} products:\n"

        return header + '\n'.join(output_lines)

    def chat(self, user_message: str, history: list = None) -> str:
        """Process user message and return response."""
        if history is None:
            history = []

        messages = [{"role": "system", "content": self._get_system_prompt()}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        # First call - let LLM decide if it needs tools
        response = self.groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=self._get_tools(),
            tool_choice="auto",
            max_tokens=1024
        )

        assistant_message = response.choices[0].message

        # Check if LLM wants to use tools
        if assistant_message.tool_calls:
            tool_call = assistant_message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            # Execute the tool
            tool_result = self._execute_tool(tool_name, tool_args)

            # For product listings: limit results if user requested specific number
            if tool_name in ["list_products", "search_products"]:
                limit = self._get_result_limit(user_message)
                result = self._limit_product_results(tool_result, limit)
                return self._clean_response(result) + "\n\nLet me know if you'd like more details on any product!"

            if tool_name == "list_orders":
                return self._clean_response(tool_result) + "\n\nLet me know if you'd like details on any specific order!"

            if tool_name == "get_order":
                return self._clean_response(tool_result)

            # For other tools, let LLM format the response
            messages.append(assistant_message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result[:1500]
            })

            final_response = self.groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                max_tokens=2048
            )
            return final_response.choices[0].message.content

        # No tools needed, return direct response
        return assistant_message.content
