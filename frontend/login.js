(function () {
    'use strict';
    var form = document.getElementById('login-form');
    var password = document.getElementById('password');
    var error = document.getElementById('login-error');
    var button = document.getElementById('login-submit');
    form.onsubmit = function (event) {
        var xhr = new XMLHttpRequest();
        event.preventDefault();
        if (!password.value || button.disabled) return;
        button.disabled = true;
        error.textContent = '';
        xhr.open('POST', '/api/auth/login', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onreadystatechange = function () {
            var response;
            if (xhr.readyState !== 4) return;
            button.disabled = false;
            if (xhr.status === 200) { window.location.replace('/'); return; }
            try { response = JSON.parse(xhr.responseText); } catch (e) { response = {}; }
            error.textContent = response.error || 'Connessione non disponibile. Riprova.';
        };
        xhr.send(JSON.stringify({password: password.value}));
    };
}());
