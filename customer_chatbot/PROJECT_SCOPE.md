# Customer Support Chatbot - Project Scope


## How to access the MCP server?

Used a curl POST request with JSON-RPC format:
```
  curl -s -X POST https://vipfapwm3x.us-east-1.awsapprunner.com/mcp \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```




## Overview
Build a prototype Customer Support chatbot for a computer products company (monitors, printers, etc.) that connects to an existing MCP server.

---

## Architecture

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐     ┌────────────┐
│   User      │────▶│  Streamlit UI   │────▶│  GROQ LLM   │────▶│ MCP Client │
│             │◀────│  (Chat Interface)│◀────│  (Intent +  │◀────│ (HTTP POST)│
└─────────────┘     └─────────────────┘     │  Response)  │     └─────┬──────┘
                                            └─────────────┘           │
                                                                      ▼
                                                              ┌────────────────┐
                                                              │   MCP Server   │
                                                              │ (Provided API) │
                                                              └────────────────┘
```

---

## What I have to Build

| Component | Description |
|-----------|-------------|
| **MCP Client** | to call MCP server tools via HTTP
| **Chatbot Logic** | GROQ LLM integration for intent detection & responses
| **Conversation Flow** | Session management, auth state, multi-turn chat
| **Streamlit UI** | Simple chat interface

---

## What's Already Provided

- **MCP Server:** `https://vipfapwm3x.us-east-1.awsapprunner.com/mcp`
- **Database:** Products, Customers, Orders (accessed via MCP)
- **API Tools:** 8 endpoints

---

## MCP Server Tools (Available)

### Products
| Tool | Purpose |
|------|---------|
| `list_products` | Browse by category, filter by active status |
| `get_product` | Get details by SKU (e.g., "COM-0001") |
| `search_products` | Keyword search |

### Customers
| Tool | Purpose |
|------|---------|
| `get_customer` | Get customer info by ID |
| `verify_customer_pin` | Authenticate with email + 4-digit PIN |

### Orders
| Tool | Purpose |
|------|---------|
| `list_orders` | View orders (filter by customer/status) |
| `get_order` | Get order details with line items |
| `create_order` | Place new order (validates inventory) |

---

## Chatbot Capabilities that I'll try to cover
- [ ] Product browsing and search
- [ ] Customer authentication (email + PIN)
- [ ] View order history (authenticated)
- [ ] Check order status

## Sample Conversations

**Product Search:**
```
User: What monitors do you have?
Bot: Here are our available monitors:
     - MON-0054: Dell 27" 4K Monitor - $449.99 (12 in stock)
     - MON-0055: LG UltraWide 34" - $599.99 (8 in stock)
```

**Authentication:**
```
User: I want to check my orders
Bot: I'll need to verify your identity. Please provide your email.
User: john@example.com
Bot: Please enter your 4-digit PIN.
User: 1234
Bot: Welcome back, John! Here are your recent orders...
```

**Order Status:**
```
User: Where's my order?
Bot: Your order #ORD-789 is currently "shipped" and expected to arrive tomorrow.
```