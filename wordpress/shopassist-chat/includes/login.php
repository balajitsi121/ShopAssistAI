<?php
/**
 * Front-end customer login page: shortcode [shopassist_login], a page that holds it, and logout links.
 * Uses WordPress's own authentication (wp_login_form), only the page and styling are custom.
 */
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

const SHOPASSIST_LOGIN_SLUG = 'customer-login';

/** Create the login page once (runs when an admin page loads, so no re-activation is needed). */
function shopassist_ensure_login_page() {
	$id = (int) get_option( 'shopassist_login_page_id', 0 );
	if ( $id && 'publish' === get_post_status( $id ) ) {
		return;
	}
	$existing = get_page_by_path( SHOPASSIST_LOGIN_SLUG );
	if ( $existing ) {
		update_option( 'shopassist_login_page_id', (int) $existing->ID );
		return;
	}
	$new_id = wp_insert_post(
		array(
			'post_type'    => 'page',
			'post_status'  => 'publish',
			'post_name'    => SHOPASSIST_LOGIN_SLUG,
			'post_title'   => 'Log in',
			'post_content' => '[shopassist_login]',
		)
	);
	if ( $new_id && ! is_wp_error( $new_id ) ) {
		update_option( 'shopassist_login_page_id', (int) $new_id );
	}
}
add_action( 'admin_init', 'shopassist_ensure_login_page' );

/** URL of the custom login page, falling back to wp-login.php if the page is missing. */
function shopassist_login_url() {
	$id = (int) get_option( 'shopassist_login_page_id', 0 );
	if ( $id && 'publish' === get_post_status( $id ) ) {
		return get_permalink( $id );
	}
	return wp_login_url();
}

/** Where to send the customer after login: ?redirect_to= if it is on this site, else the home page. */
function shopassist_login_redirect_target() {
	// phpcs:ignore WordPress.Security.NonceVerification.Recommended -- plain redirect target, validated below.
	$wanted = isset( $_GET['redirect_to'] ) ? esc_url_raw( wp_unslash( $_GET['redirect_to'] ) ) : '';
	return wp_validate_redirect( $wanted, home_url( '/' ) );
}

/** Mark our form so the failure hooks below only react to it. */
function shopassist_login_form_marker() {
	return '<input type="hidden" name="shopassist_login" value="1">';
}
add_filter( 'login_form_top', 'shopassist_login_form_marker' );

/** Wrong password or unknown user: come back to our page with an error flag instead of wp-login.php. */
function shopassist_login_failed( $username ) {
	if ( empty( $_POST['shopassist_login'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Missing
		return;
	}
	wp_safe_redirect( add_query_arg( 'login', 'failed', shopassist_login_url() ) );
	exit;
}
add_action( 'wp_login_failed', 'shopassist_login_failed' );

/** Empty username or password: same, with a different message. */
function shopassist_login_empty( $user, $username, $password ) {
	if ( empty( $_POST['shopassist_login'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Missing
		return $user;
	}
	if ( '' === $username || '' === $password ) {
		wp_safe_redirect( add_query_arg( 'login', 'empty', shopassist_login_url() ) );
		exit;
	}
	return $user;
}
add_filter( 'authenticate', 'shopassist_login_empty', 99, 3 );

function shopassist_login_styles() {
	return '<style>
.sa-login-box{max-width:420px;margin:32px auto;padding:28px;border:1px solid #d9dee3;border-radius:10px;background:#fff;box-shadow:0 2px 10px rgba(0,0,0,.05)}
.sa-login-box h2{margin:0 0 6px;font-size:1.5rem}
.sa-login-box p.sa-lead{margin:0 0 18px;color:#5b6670}
.sa-login-box label{display:block;margin:0 0 6px;font-weight:600}
.sa-login-box input[type=text],.sa-login-box input[type=password]{width:100%;padding:11px 12px;border:1px solid #c5ccd3;border-radius:6px;font-size:1rem;box-sizing:border-box}
.sa-login-box input:focus{outline:none;border-color:#0f766e;box-shadow:0 0 0 3px rgba(15,118,110,.18)}
.sa-login-box .login-username,.sa-login-box .login-password{margin:0 0 16px}
.sa-login-box .login-remember{margin:0 0 16px}
.sa-login-box .login-remember label{display:inline;font-weight:400}
.sa-login-box input[type=submit]{width:100%;padding:13px;border:0;border-radius:6px;background:#0f766e;color:#fff;font-size:1rem;font-weight:700;cursor:pointer}
.sa-login-box input[type=submit]:hover{background:#0b4f4a}
.sa-login-error{margin:0 0 16px;padding:10px 12px;border-radius:6px;background:#fdecea;color:#8a1f17}
.sa-login-links{margin:16px 0 0;font-size:.9rem}
.sa-login-box .sa-btn{display:inline-block;margin-top:10px;padding:11px 18px;border-radius:6px;background:#0f766e;color:#fff;text-decoration:none;font-weight:700}
</style>';
}

/** [shopassist_login] */
function shopassist_login_shortcode() {
	$out = shopassist_login_styles() . '<div class="sa-login-box">';

	if ( is_user_logged_in() ) {
		$user = wp_get_current_user();
		$out .= '<h2>You are signed in</h2>';
		$out .= '<p class="sa-lead">Signed in as ' . esc_html( $user->display_name ) . '. Open the chat at the bottom right to ask about your orders.</p>';
		$out .= '<a class="sa-btn" href="' . esc_url( home_url( '/' ) ) . '">Continue shopping</a> ';
		$out .= '<a class="sa-btn" style="background:#475569" href="' . esc_url( wp_logout_url( home_url( '/' ) ) ) . '">Log out</a>';
		return $out . '</div>';
	}

	// phpcs:ignore WordPress.Security.NonceVerification.Recommended -- display-only flag.
	$flag = isset( $_GET['login'] ) ? sanitize_key( wp_unslash( $_GET['login'] ) ) : '';
	$out .= '<h2>Log in</h2><p class="sa-lead">Log in to see and ask about your orders.</p>';
	if ( 'failed' === $flag ) {
		$out .= '<div class="sa-login-error" role="alert">The username or password is not correct. Please try again.</div>';
	} elseif ( 'empty' === $flag ) {
		$out .= '<div class="sa-login-error" role="alert">Please enter your username and password.</div>';
	}

	$out .= wp_login_form(
		array(
			'echo'           => false,
			'redirect'       => shopassist_login_redirect_target(),
			'label_username' => 'Username or email',
			'label_password' => 'Password',
			'label_remember' => 'Keep me signed in',
			'label_log_in'   => 'Log in',
			'remember'       => true,
		)
	);
	$out .= '<p class="sa-login-links"><a href="' . esc_url( wp_lostpassword_url() ) . '">Forgot your password?</a></p>';
	return $out . '</div>';
}
add_shortcode( 'shopassist_login', 'shopassist_login_shortcode' );
