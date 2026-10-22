<?php
/**
 * WooCommerce glue: shows ShopAssist order numbers, and builds the signed-in customer's
 * order list that is sent to the ShopAssist API with each chat message.
 */
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * ORD-xxxx number shown in WooCommerce and used by the assistant.
 * Seeded demo orders keep their ORD-1001 style number; real orders become ORD-<id>.
 */
function shopassist_order_ref( $order ) {
	$ref = $order->get_meta( '_shopassist_order_id' );
	return $ref ? $ref : 'ORD-' . str_pad( (string) $order->get_id(), 4, '0', STR_PAD_LEFT );
}

function shopassist_wc_order_number( $order_number, $order ) {
	return shopassist_order_ref( $order );
}
add_filter( 'woocommerce_order_number', 'shopassist_wc_order_number', 10, 2 );

/** Date as Y-m-d, or null. */
function shopassist_ymd( $date ) {
	return $date ? $date->date( 'Y-m-d' ) : null;
}

/** Non-empty string meta value or null. */
function shopassist_meta_or_null( $order, $key ) {
	$value = $order->get_meta( $key );
	return '' === $value ? null : (string) $value;
}

/**
 * Convert one WooCommerce order to the shape the ShopAssist API expects.
 * Status: the demo "shipped" detail is kept in meta (WooCommerce has no Shipped status).
 */
function shopassist_map_order( $order ) {
	$wc_status = $order->get_status();
	$status    = $order->get_meta( '_shopassist_status' );
	if ( ! in_array( $status, array( 'Processing', 'Shipped', 'Delivered', 'Cancelled' ), true ) ) {
		if ( 'completed' === $wc_status ) {
			$status = 'Delivered';
		} elseif ( in_array( $wc_status, array( 'cancelled', 'refunded', 'failed' ), true ) ) {
			$status = 'Cancelled';
		} else {
			$status = 'Processing'; // pending, on-hold, processing.
		}
	}

	$items = array_values( $order->get_items() );
	$first = $items ? $items[0] : null;
	$name  = $first ? $first->get_name() : 'Order items';
	if ( count( $items ) > 1 ) {
		$name .= ' (+' . ( count( $items ) - 1 ) . ' more)';
	}

	$category   = $order->get_meta( '_shopassist_category' );
	$final_sale = '1' === $order->get_meta( '_shopassist_final_sale' );
	if ( '' === $category && $first && $first->get_product() ) {
		$terms = wc_get_product_terms( $first->get_product()->get_id(), 'product_cat', array( 'fields' => 'slugs' ) );
		if ( $terms ) {
			$category = $terms[0];
		}
		$final_sale = $final_sale || in_array( 'clearance', (array) $terms, true );
	}

	$delivered = shopassist_meta_or_null( $order, '_shopassist_delivered_on' );
	if ( null === $delivered && 'Delivered' === $status ) {
		$delivered = shopassist_ymd( $order->get_date_completed() );
	}

	return array(
		'order_id'           => shopassist_order_ref( $order ),
		'status'             => $status,
		'item'               => $name,
		'category'           => $category ? $category : null,
		'final_sale'         => $final_sale,
		'ordered_on'         => shopassist_ymd( $order->get_date_created() ),
		'shipped_on'         => shopassist_meta_or_null( $order, '_shopassist_shipped_on' ),
		'delivered_on'       => $delivered,
		'estimated_delivery' => shopassist_meta_or_null( $order, '_shopassist_estimated_delivery' ),
		'total'              => (float) $order->get_total(),
	);
}

/**
 * The signed-in customer's own orders (newest first, max 50). Empty for guests or without WooCommerce.
 * This is the only place order data is chosen: it is always filtered by the logged-in user's ID.
 */
function shopassist_customer_orders( $user_id ) {
	if ( ! $user_id || ! function_exists( 'wc_get_orders' ) ) {
		return array();
	}
	$orders = wc_get_orders(
		array(
			'customer_id' => (int) $user_id,
			'limit'       => 50,
			'orderby'     => 'date',
			'order'       => 'DESC',
			'type'        => 'shop_order',
		)
	);
	return array_map( 'shopassist_map_order', $orders );
}
