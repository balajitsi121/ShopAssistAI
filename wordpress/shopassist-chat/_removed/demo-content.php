<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Sample orders. They match data/orders.json in the ShopAssist project.
 */
function shopassist_demo_orders() {
	return array(
		array( 'id' => 'ORD-1001', 'item' => 'Desk lamp',          'status' => 'Shipped',    'total' => 2499, 'sku' => 'SA-LAMP' ),
		array( 'id' => 'ORD-1002', 'item' => 'Running shoes',      'status' => 'Delivered',  'total' => 1499, 'sku' => 'SA-SHOES' ),
		array( 'id' => 'ORD-1003', 'item' => 'Clearance backpack', 'status' => 'Delivered',  'total' => 899,  'sku' => 'SA-BAG' ),
		array( 'id' => 'ORD-1004', 'item' => 'Rain jacket',        'status' => 'Processing', 'total' => 3299, 'sku' => 'SA-JACKET' ),
	);
}

function shopassist_policy_html() {
	return '<h2>1. Eligibility</h2><p>Items can be returned if they are unused and in original packaging. Items marked final sale cannot be returned.</p>'
		. '<h2>2. Return window</h2><p>Items can be returned within 30 days of delivery.</p>'
		. '<h2>3. How to start a return</h2><p>Contact support with your order number. Returns are not started by the chat assistant.</p>'
		. '<h2>4. Refund procedure</h2><p>Refunds are issued to the original payment method after the returned item is received and inspected.</p>'
		. '<p><em>Sample policy for the ShopAssist AI demo.</em></p>';
}

function shopassist_orders_html() {
	$rows = '';
	foreach ( shopassist_demo_orders() as $order ) {
		$rows .= sprintf(
			'<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>',
			esc_html( $order['id'] ),
			esc_html( $order['item'] ),
			esc_html( $order['status'] ),
			esc_html( number_format_i18n( $order['total'] ) )
		);
	}
	return '<p>Use these sample order numbers when you ask the ShopAssist chat about an order.</p>'
		. '<table><thead><tr><th>Order</th><th>Item</th><th>Status</th><th>Total</th></tr></thead><tbody>' . $rows . '</tbody></table>';
}

/**
 * Create a page unless one with the same slug already exists. Returns true if created.
 */
function shopassist_create_page( $slug, $title, $content ) {
	if ( get_page_by_path( $slug ) ) {
		return false;
	}
	wp_insert_post(
		array(
			'post_type'    => 'page',
			'post_status'  => 'publish',
			'post_name'    => $slug,
			'post_title'   => $title,
			'post_content' => $content,
		)
	);
	return true;
}

/**
 * Create the demo pages and (if WooCommerce is active) the demo products.
 */
function shopassist_create_demo_content() {
	$pages    = (int) shopassist_create_page( 'returns-policy', 'Returns Policy', shopassist_policy_html() );
	$pages   += (int) shopassist_create_page( 'demo-orders', 'Demo Orders', shopassist_orders_html() );
	$products = 0;

	if ( class_exists( 'WC_Product_Simple' ) ) {
		foreach ( shopassist_demo_orders() as $order ) {
			if ( wc_get_product_id_by_sku( $order['sku'] ) ) {
				continue;
			}
			$product = new WC_Product_Simple();
			$product->set_name( $order['item'] );
			$product->set_sku( $order['sku'] );
			$product->set_regular_price( (string) $order['total'] );
			$product->set_status( 'publish' );
			$product->save();
			++$products;
		}
	}
	return array( $pages, $products );
}

function shopassist_handle_demo() {
	if ( ! current_user_can( 'manage_options' ) ) {
		wp_die( 'Not allowed.' );
	}
	check_admin_referer( 'shopassist_demo' );

	list( $pages, $products ) = shopassist_create_demo_content();
	$note = class_exists( 'WC_Product_Simple' ) ? '' : ' WooCommerce is not active, so no products were created.';
	shopassist_redirect( true, sprintf( 'Demo content created: %d page(s), %d product(s).%s', $pages, $products, $note ) );
}
add_action( 'admin_post_shopassist_demo', 'shopassist_handle_demo' );
