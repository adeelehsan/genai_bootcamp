"""
MCP Client for Customer Support Chatbot
Handles JSON-RPC communication with the MCP server.
"""

import requests
from typing import Optional, Dict, Any, List


class MCPClient:
    """Client for communicating with the MCP server."""

    def __init__(self, base_url: str = "https://vipfapwm3x.us-east-1.awsapprunner.com/mcp"):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self._request_id = 0

    def _get_request_id(self) -> int:
        """Generate unique request ID."""
        self._request_id += 1
        return self._request_id

    def _call(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make JSON-RPC call to MCP server."""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self._get_request_id()
        }
        if params:
            payload["params"] = params

        response = requests.post(self.base_url, json=payload, headers=self.headers)
        response.raise_for_status()
        result = response.json()

        if "error" in result:
            raise Exception(f"MCP Error: {result['error']}")

        return result.get("result", {})

    def call_tool(self, tool_name: str, arguments: Optional[Dict] = None) -> str:
        """Call a specific MCP tool."""
        params = {"name": tool_name}
        if arguments:
            params["arguments"] = arguments

        result = self._call("tools/call", params)

        # Handle MCP response structure: result.content[0].text
        content = result.get("content", [])
        if content and len(content) > 0:
            return content[0].get("text", "")
        return ""

    # Product Tools
    def list_products(self, category: Optional[str] = None, is_active: Optional[bool] = None) -> str:
        """List products with optional filters."""
        args = {}
        if category:
            args["category"] = category
        if is_active is not None:
            args["is_active"] = is_active
        return self.call_tool("list_products", args if args else None)

    def get_product(self, sku: str) -> str:
        """Get product details by SKU."""
        return self.call_tool("get_product", {"sku": sku})

    def search_products(self, query: str) -> str:
        """Search products by keyword."""
        # Handle plurals - strip trailing 's' if no results
        result = self.call_tool("search_products", {"query": query})
        if "No products found" in result and query.endswith('s'):
            result = self.call_tool("search_products", {"query": query[:-1]})
        return result

    # Customer Tools
    def get_customer(self, customer_id: str) -> str:
        """Get customer info by ID."""
        return self.call_tool("get_customer", {"customer_id": customer_id})

    def verify_customer_pin(self, email: str, pin: str) -> str:
        """Verify customer with email and PIN."""
        return self.call_tool("verify_customer_pin", {"email": email, "pin": pin})

    # Order Tools
    def list_orders(self, customer_id: Optional[str] = None, status: Optional[str] = None) -> str:
        """List orders with optional filters."""
        args = {}
        if customer_id:
            args["customer_id"] = customer_id
        if status:
            args["status"] = status
        return self.call_tool("list_orders", args if args else None)

    def get_order(self, order_id: str) -> str:
        """Get order details by ID."""
        return self.call_tool("get_order", {"order_id": order_id})

    def create_order(self, customer_id: str, items: List[Dict]) -> str:
        """Create a new order."""
        return self.call_tool("create_order", {
            "customer_id": customer_id,
            "items": items
        })
