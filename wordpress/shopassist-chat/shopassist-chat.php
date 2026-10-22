<?php
/**
 * Plugin Name: ShopAssist Chat
 * Description: Floating AI chat widget for the ShopAssist AI proof of concept. Shows the logged-in customer's WooCommerce orders to the assistant.
 * Version: 1.1.0
 * Requires PHP: 7.4
 * Text Domain: shopassist-chat
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'SHOPASSIST_VERSION', '1.1.0' );
define( 'SHOPASSIST_DIR', plugin_dir_path( __FILE__ ) );
define( 'SHOPASSIST_URL', plugin_dir_url( __FILE__ ) );

require_once SHOPASSIST_DIR . 'includes/settings.php';
require_once SHOPASSIST_DIR . 'includes/rest.php';
require_once SHOPASSIST_DIR . 'includes/woo-orders.php';
require_once SHOPASSIST_DIR . 'includes/login.php';

/**
 * Load the widget CSS/JS on every front-end page and pass it its settings.
 */
function shopassist_enqueue_assets() {
	wp_enqueue_style( 'shopassist-chat', SHOPASSIST_URL . 'assets/chat.css', array(), SHOPASSIST_VERSION );
	wp_enqueue_script( 'shopassist-chat', SHOPASSIST_URL . 'assets/chat.js', array(), SHOPASSIST_VERSION, true );
	wp_localize_script(
		'shopassist-chat',
		'ShopAssistConfig',
		array(
			'restUrl'     => esc_url_raw( rest_url( 'shopassist/v1/chat' ) ),
			'nonce'       => wp_create_nonce( 'wp_rest' ),
			'showDetails' => (bool) get_option( 'shopassist_show_details', 1 ),
			'loggedIn'    => is_user_logged_in(),
			'userName'    => is_user_logged_in() ? wp_get_current_user()->display_name : '',
			'loginUrl'    => shopassist_login_url(),
			'logoutUrl'   => is_user_logged_in() ? wp_logout_url( home_url( '/' ) ) : '',
		)
	);
}
add_action( 'wp_enqueue_scripts', 'shopassist_enqueue_assets' );

/**
 * Container the widget script attaches to.
 */
function shopassist_render_root() {
	echo '<div id="shopassist-root"></div>';
}
add_action( 'wp_footer', 'shopassist_render_root' );
