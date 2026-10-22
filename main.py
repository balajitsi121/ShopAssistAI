from tools.order_tools import get_order_details

order = get_order_details("ORD-1001");

if order is not None:
    print(f"Order Status: {order['status']}")
    print(f"Order total: ₹{order['total']}")
else:
    print("Order not found");
