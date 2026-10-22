/**
 * ShopAssist Chat widget: floating bubble + chat panel.
 * Talks to the WordPress REST route, which forwards to the ShopAssist API.
 */
(function () {
	'use strict';

	var config = window.ShopAssistConfig || {};
	var root = document.getElementById('shopassist-root');
	if (!root || !config.restUrl) {
		return;
	}

	var history = []; // [{role, content}] sent with each request so the agent remembers the conversation
	var STARTERS = config.loggedIn
		? ['Where is my latest order?', 'Which of my orders can I return?', 'How long do refunds take?']
		: ['What is your return policy?', 'How long do refunds take?', 'Can final-sale items be returned?'];

	/** Small helper to create an element with a class and optional text. */
	function el(tag, className, text) {
		var node = document.createElement(tag);
		if (className) { node.className = className; }
		if (text) { node.textContent = text; }
		return node;
	}

	// ---- build the widget -------------------------------------------------------------------
	var toggle = el('button', 'sa-toggle', 'Chat');
	toggle.type = 'button';
	toggle.setAttribute('aria-label', 'Open ShopAssist chat');
	toggle.setAttribute('aria-expanded', 'false');
	toggle.setAttribute('aria-controls', 'sa-panel');

	var panel = el('div', 'sa-panel');
	panel.id = 'sa-panel';
	panel.setAttribute('role', 'dialog');
	panel.setAttribute('aria-label', 'ShopAssist chat');
	panel.hidden = true;

	var header = el('div', 'sa-header');
	var titleBox = el('div', 'sa-header-text');
	titleBox.appendChild(el('strong', 'sa-title', 'ShopAssist'));
	titleBox.appendChild(el('span', 'sa-subtitle', config.loggedIn ? 'Signed in as ' + config.userName : 'Guest · log in to see your orders'));
	var closeBtn = el('button', 'sa-close', '×');
	closeBtn.type = 'button';
	closeBtn.setAttribute('aria-label', 'Close chat');
	header.appendChild(titleBox);
	if (config.loggedIn && config.logoutUrl) {
		var logout = el('a', 'sa-logout', 'Log out');
		logout.href = config.logoutUrl;
		logout.setAttribute('aria-label', 'Log out of your account');
		header.appendChild(logout);
	}
	header.appendChild(closeBtn);

	var log = el('div', 'sa-log');
	log.setAttribute('role', 'log');
	log.setAttribute('aria-live', 'polite');

	var starters = el('div', 'sa-starters');

	var form = el('form', 'sa-form');
	var input = el('input', 'sa-input');
	input.type = 'text';
	input.maxLength = 1000;
	input.placeholder = 'Ask about an order or a return';
	input.setAttribute('aria-label', 'Your message');
	var sendBtn = el('button', 'sa-send', 'Send');
	sendBtn.type = 'submit';
	form.appendChild(input);
	form.appendChild(sendBtn);

	panel.appendChild(header);
	panel.appendChild(log);
	panel.appendChild(starters);
	panel.appendChild(form);
	root.appendChild(panel);
	root.appendChild(toggle);

	// ---- rendering --------------------------------------------------------------------------
	function scrollToEnd() {
		log.scrollTop = log.scrollHeight;
	}

	/** Show the tools used and the policy sections cited under an answer. */
	function renderDetails(box, trace) {
		if (!config.showDetails || !trace || !trace.length) { return; }
		var details = el('div', 'sa-details');
		var sources = {};
		trace.forEach(function (step) {
			var args = Object.keys(step.args || {}).map(function (k) { return "'" + step.args[k] + "'"; }).join(', ');
			details.appendChild(el('span', 'sa-chip', 'tool: ' + step.tool + '(' + args + ')'));
			(step.sources || []).forEach(function (s) { sources[s.source + ' · ' + s.section] = true; });
		});
		var names = Object.keys(sources);
		if (names.length) {
			var line = el('div', 'sa-sources');
			line.appendChild(el('span', 'sa-label', 'Sources:'));
			names.forEach(function (name) { line.appendChild(el('span', 'sa-source', name)); });
			details.appendChild(line);
		}
		box.appendChild(details);
	}

	function addMessage(role, text, trace) {
		var box = el('div', 'sa-msg sa-' + role);
		box.appendChild(el('div', 'sa-bubble', text));
		if (role === 'bot') { renderDetails(box, trace); }
		log.appendChild(box);
		scrollToEnd();
		return box;
	}

	function setBusy(busy) {
		input.disabled = busy;
		sendBtn.disabled = busy;
		form.classList.toggle('sa-busy', busy);
	}

	// ---- talking to the server --------------------------------------------------------------
	function send(text) {
		text = (text || '').trim();
		if (!text) { return; }
		starters.hidden = true;
		addMessage('user', text);
		var typing = addMessage('bot', 'Thinking…');
		typing.classList.add('sa-typing');
		setBusy(true);

		fetch(config.restUrl, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json', 'X-WP-Nonce': config.nonce },
			body: JSON.stringify({ message: text, history: history.slice(-10) })
		})
			.then(function (response) {
				return response.json().catch(function () { return {}; });
			})
			.then(function (data) {
				var answer = data.answer || 'Sorry, something went wrong. Please try again.';
				typing.remove();
				addMessage('bot', answer, data.trace);
				history.push({ role: 'user', content: text }, { role: 'assistant', content: answer });
			})
			.catch(function () {
				typing.remove();
				addMessage('bot', 'Sorry, I could not reach the assistant. Please try again.');
			})
			.then(function () {
				setBusy(false);
				input.value = '';
				input.focus();
			});
	}

	// ---- events -----------------------------------------------------------------------------
	function setOpen(open) {
		panel.hidden = !open;
		toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
		toggle.classList.toggle('sa-hidden', open);
		if (open) { input.focus(); } else { toggle.focus(); }
	}

	toggle.addEventListener('click', function () { setOpen(true); });
	closeBtn.addEventListener('click', function () { setOpen(false); });
	panel.addEventListener('keydown', function (event) {
		if (event.key === 'Escape') { setOpen(false); }
	});
	form.addEventListener('submit', function (event) {
		event.preventDefault();
		send(input.value);
	});

	STARTERS.forEach(function (question) {
		var button = el('button', 'sa-starter', question);
		button.type = 'button';
		button.addEventListener('click', function () { send(question); });
		starters.appendChild(button);
	});

	if (config.loggedIn) {
		addMessage('bot', 'Hi ' + config.userName + '! I can check the status of your orders, tell you whether an item can be returned, or explain our return policy.');
	} else {
		var hello = addMessage('bot', 'Hi! I can explain our return policy. To check your orders, please log in to your account.');
		var link = el('a', 'sa-login', 'Log in to see my orders');
		var base = config.loginUrl || '/wp-login.php';
		link.href = base + (base.indexOf('?') === -1 ? '?' : '&') + 'redirect_to=' + encodeURIComponent(window.location.href);
		hello.appendChild(link);
	}
})();
