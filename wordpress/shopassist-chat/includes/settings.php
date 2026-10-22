<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Register the plugin settings (Settings > ShopAssist Chat).
 */
function shopassist_register_settings() {
	register_setting(
		'shopassist',
		'shopassist_api_url',
		array(
			'type'              => 'string',
			'sanitize_callback' => 'esc_url_raw',
			'default'           => 'http://localhost:8000',
		)
	);
	register_setting(
		'shopassist',
		'shopassist_api_key',
		array(
			'type'              => 'string',
			'sanitize_callback' => 'sanitize_text_field',
			'default'           => '',
		)
	);
	register_setting(
		'shopassist',
		'shopassist_show_details',
		array(
			'type'              => 'boolean',
			'sanitize_callback' => 'rest_sanitize_boolean',
			'default'           => true,
		)
	);
}
add_action( 'admin_init', 'shopassist_register_settings' );

function shopassist_add_settings_page() {
	add_options_page( 'ShopAssist Chat', 'ShopAssist Chat', 'manage_options', 'shopassist', 'shopassist_render_settings_page' );
}
add_action( 'admin_menu', 'shopassist_add_settings_page' );

/**
 * Show the result of the "test connection" and "create demo content" buttons.
 */
function shopassist_render_notices() {
	// phpcs:ignore WordPress.Security.NonceVerification.Recommended -- display-only flags.
	$result = isset( $_GET['shopassist_result'] ) ? sanitize_text_field( wp_unslash( $_GET['shopassist_result'] ) ) : '';
	// phpcs:ignore WordPress.Security.NonceVerification.Recommended
	$detail = isset( $_GET['shopassist_detail'] ) ? sanitize_text_field( wp_unslash( $_GET['shopassist_detail'] ) ) : '';
	if ( '' === $result ) {
		return;
	}
	$class = ( 'ok' === $result ) ? 'notice-success' : 'notice-error';
	printf( '<div class="notice %s"><p>%s</p></div>', esc_attr( $class ), esc_html( $detail ) );
}

function shopassist_render_settings_page() {
	if ( ! current_user_can( 'manage_options' ) ) {
		return;
	}
	?>
	<div class="wrap">
		<h1>ShopAssist Chat</h1>
		<?php shopassist_render_notices(); ?>

		<form method="post" action="options.php">
			<?php settings_fields( 'shopassist' ); ?>
			<table class="form-table" role="presentation">
				<tr>
					<th scope="row"><label for="shopassist_api_url">API URL</label></th>
					<td>
						<input name="shopassist_api_url" id="shopassist_api_url" type="url" class="regular-text"
							value="<?php echo esc_attr( get_option( 'shopassist_api_url', 'http://localhost:8000' ) ); ?>">
						<p class="description">Where the ShopAssist API runs, for example http://dev-server:8000 (no trailing slash needed).</p>
					</td>
				</tr>
				<tr>
					<th scope="row"><label for="shopassist_api_key">API key</label></th>
					<td>
						<input name="shopassist_api_key" id="shopassist_api_key" type="password" class="regular-text" autocomplete="off"
							value="<?php echo esc_attr( get_option( 'shopassist_api_key', '' ) ); ?>">
						<p class="description">Must match SHOPASSIST_API_KEY in the API's .env file. Leave empty if the API has no key.</p>
					</td>
				</tr>
				<tr>
					<th scope="row">Show tool calls</th>
					<td>
						<label>
							<input name="shopassist_show_details" type="checkbox" value="1" <?php checked( get_option( 'shopassist_show_details', 1 ) ); ?>>
							Show the tools used and policy sources under each answer (useful for demos)
						</label>
					</td>
				</tr>
			</table>
			<?php submit_button(); ?>
		</form>

		<hr>
		<h2>Tools</h2>
		<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" style="display:inline-block;margin-right:12px">
			<input type="hidden" name="action" value="shopassist_test">
			<?php wp_nonce_field( 'shopassist_test' ); ?>
			<?php submit_button( 'Test connection', 'secondary', 'submit', false ); ?>
		</form>
		<p class="description">Signed-in customers can ask about their own WooCommerce orders. Guests can only ask about the return policy.</p>
	</div>
	<?php
}

/**
 * Redirect back to the settings page with a message.
 */
function shopassist_redirect( $ok, $detail ) {
	wp_safe_redirect(
		add_query_arg(
			array(
				'page'              => 'shopassist',
				'shopassist_result' => $ok ? 'ok' : 'error',
				'shopassist_detail' => rawurlencode( $detail ),
			),
			admin_url( 'options-general.php' )
		)
	);
	exit;
}

/**
 * "Test connection" button: call the API's /health endpoint.
 */
function shopassist_handle_test() {
	if ( ! current_user_can( 'manage_options' ) ) {
		wp_die( 'Not allowed.' );
	}
	check_admin_referer( 'shopassist_test' );

	$base     = untrailingslashit( get_option( 'shopassist_api_url', 'http://localhost:8000' ) );
	$response = wp_remote_get( $base . '/health', array( 'timeout' => 10, 'headers' => array( 'ngrok-skip-browser-warning' => '1' ) ) );

	if ( is_wp_error( $response ) ) {
		shopassist_redirect( false, 'Could not reach the API: ' . $response->get_error_message() );
	}
	$code = wp_remote_retrieve_response_code( $response );
	if ( 200 === $code ) {
		shopassist_redirect( true, 'Connected. The ShopAssist API is running.' );
	}
	shopassist_redirect( false, 'The API answered with HTTP ' . $code . '. Check the URL.' );
}
add_action( 'admin_post_shopassist_test', 'shopassist_handle_test' );
