# Design Decisions

## 1. Tool Calling via GROQ Native Function Calling
We use GROQ's built-in function calling feature instead of manual intent detection. The LLM automatically decides when to call tools (list_products, search_products, etc.) based on user input.

## 2. Product Display Limited to Top 10 Results
The MCP server returns up to 200 products. We limit display to 10 to avoid overwhelming users and keep responses readable.

## 3. Search Fallback for Plurals
The MCP server does exact substring matching, so "monitors" fails but "monitor" works. We automatically retry without the trailing 's' when no results are found.

## 4. Tool Result Size Capped at 3000 Characters
Large tool responses can overflow the LLM context window. We truncate results to 3000 characters to ensure the model can process and respond properly.
