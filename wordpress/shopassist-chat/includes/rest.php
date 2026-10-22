<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * The browser talks to WordPress, and WordPress calls the ShopAssist API from the server.
 * This keeps the API URL and key out of the page and avoids CORS problems.
 */
function shopassist_register_routes() {
	register_rest_route(
		'shopassist/v1',
		'/chat',
		array(
			'methods'             => 'POST',
			'callback'            => 'shopassist_handle_chat',
			'permission_callback' => '__return_true', // Public demo widget; protected by a rate limit instead.
		)
	);
}
add_action( 'rest_api_init', 'shopassist_register_routes' );

/**
 * Allow at most 20 messages per minute per visitor IP.
 */
function shopassist_rate_limited() {
	$ip    = isset( $_SERVER['REMOTE_ADDR'] ) ? sanitize_text_field( wp_unslash( $_SERVER['REMOTE_ADDR'] ) ) : 'unknown';
	$key   = 'shopassist_rl_' . md5( $ip );
	$count = (int) get_transient( $key );
	if ( $count >= 20 ) {
		return true;
	}
	set_transient( $key, $count + 1, MINUTE_IN_SECONDS );
	return false;
}

function shopassist_reply( $answer, $trace = array(), $status = 200 ) {
	return new WP_REST_Response( array( 'answer' => $answer, 'trace' => $trace ), $status );
}

/**
 * Keep only the last 10 well-formed turns of the conversation.
 */
function shopassist_clean_history( $raw ) {
	$history = array();
	if ( ! is_array( $raw ) ) {
		return $history;
	}
	foreach ( array_slice( $raw, -10 ) as $turn ) {
		if ( ! is_array( $turn ) ) {
			continue;
		}
		$role    = ( isset( $turn['role'] ) && 'assistant' === $turn['role'] ) ? 'assistant' : 'user';
		$content = isset( $turn['content'] ) ? mb_substr( sanitize_textarea_field( (string) $turn['content'] ), 0, 2000 ) : '';
		if ( '' !== $content ) {
			$history[] = array( 'role' => $role, 'content' => $content );
		}
	}
	return $history;
}

function shopassist_handle_chat( WP_REST_Request $request ) {
	if ( shopassist_rate_limited() ) {
		return shopassist_reply( 'You are sending messages too quickly. Please wait a minute and try again.', array(), 429 );
	}

	$message = mb_substr( sanitize_textarea_field( (string) $request->get_param( 'message' ) ), 0, 1000 );
	if ( '' === $message ) {
		return shopassist_reply( 'Please type a question.', array(), 400 );
	}

	$base    = untrailingslashit( get_option( 'shopassist_api_url', 'http://localhost:8000' ) );
	// ngrok's free plan shows a browser warning page unless this header is sent; other hosts ignore it.
	$headers = array( 'Content-Type' => 'application/json', 'ngrok-skip-browser-warning' => '1' );
	$key     = get_option( 'shopassist_api_key', '' );
	if ( '' !== $key ) {
		$headers['X-API-Key'] = $key;
	}

	// Orders come only from the server, for the logged-in user. Anything the browser sends is ignored.
	$user_id = get_current_user_id();
	$user    = $user_id ? wp_get_current_user() : null;

	$response = wp_remote_post(
		$base . '/chat',
		array(
			'timeout' => 60,
			'headers' => $headers,
			'body'    => wp_json_encode(
				array(
					'message'       => $message,
					'history'       => shopassist_clean_history( $request->get_param( 'history' ) ),
					'orders'        => shopassist_customer_orders( $user_id ), // [] for guests: they see no orders.
					'customer_name' => $user ? $user->display_name : null,
				)
			),
		)
	);

	$fail = 'Sorry, the assistant is not available right now. Please try again in a moment.';
	if ( is_wp_error( $response ) || 200 !== wp_remote_retrieve_response_code( $response ) ) {
		return shopassist_reply( $fail, array(), 502 );
	}
	$data = json_decode( wp_remote_retrieve_body( $response ), true );
	if ( ! is_array( $data ) || empty( $data['answer'] ) ) {
		return shopassist_reply( $fail, array(), 502 );
	}
	return shopassist_reply( (string) $data['answer'], isset( $data['trace'] ) && is_array( $data['trace'] ) ? $data['trace'] : array() );
}
