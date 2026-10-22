# ShopAssist Chat (WordPress plugin)

Floating chat bubble for the ShopAssist AI proof of concept.

- Settings: Settings > ShopAssist Chat (API URL, API key, show tool calls) and a Test connection button.
- Signed-in customers: WordPress sends that customer's own WooCommerce orders (matched by user ID) to the ShopAssist API with each message, so the assistant can only see and discuss their orders.
- Guests: no orders are sent. They can ask about the return policy and are asked to log in.
- Order numbers: seeded demo orders keep ORD-1001 style numbers; other orders show as ORD-<id>.
- The browser calls `/wp-json/shopassist/v1/chat`; WordPress forwards to the ShopAssist API. The browser can never supply orders.
- The old "Create demo content" button and sample-orders page were removed.
