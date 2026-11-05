/* ES5 and XMLHttpRequest keep the interface usable on older versions of Safari. */
(function () {
    'use strict';
    var chats = document.getElementById('chats');
    var messages = document.getElementById('messages');
    var status = document.getElementById('status');
    var input = document.getElementById('message');
    var send = document.getElementById('send');
    var sidebar = document.getElementById('sidebar');
    var app = document.getElementById('app');
    var menu = document.getElementById('menu');
    var active = null;
    var busy = false;
    var list = [];
    var loadVersion = 0;
    var currentItems = [];

    function updateMenu() {
        var open = window.innerWidth <= 700 ? sidebar.className === 'sidebar open' : app.className !== 'app sidebar-closed';
        var label = open ? 'Chiudi conversazioni' : 'Apri conversazioni';
        var heading = document.getElementById('sidebar-heading');
        if (open && heading.offsetHeight) chats.style.top = (heading.offsetTop + heading.offsetHeight + 14) + 'px';
        menu.setAttribute('aria-expanded', open ? 'true' : 'false');
        menu.setAttribute('aria-label', label);
        menu.title = label;
        document.getElementById('menu-icon').src = open ? 'sidebar-open.svg' : 'sidebar-closed.svg';
    }

    function request(method, url, data, callback) {
        var xhr = new XMLHttpRequest();
        var finished = false;
        function finish(error, result) {
            if (finished) return;
            finished = true;
            callback(error, result);
        }
        xhr.open(method, url, true);
        xhr.timeout = 120000;
        if (data) xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onreadystatechange = function () {
            var result;
            if (xhr.readyState !== 4) return;
            if (xhr.status === 401) { window.location.replace('/login.html'); return; }
            try { result = JSON.parse(xhr.responseText); } catch (error) { result = {}; }
            finish(xhr.status >= 200 && xhr.status < 300 ? null : (result.error || 'Errore di connessione. Riprova.'), result);
        };
        xhr.ontimeout = function () { finish('La richiesta ha impiegato troppo tempo. Riprova.', {}); };
        xhr.onerror = function () { finish('Errore di connessione. Riprova.', {}); };
        xhr.send(data ? JSON.stringify(data) : null);
    }

    function element(tag, className, text) {
        var node = document.createElement(tag);
        if (className) node.className = className;
        if (typeof text !== 'undefined') node.textContent = text;
        return node;
    }

    function mark(className) {
        var image = element('img', className);
        image.src = 'mark.svg?v=2';
        image.alt = '';
        return image;
    }

    // Marked 0.3.x supports ES5. Raw HTML is escaped; links only allow HTTP(S).
    function markdownRenderer(noLinks) {
        var renderer = new marked.Renderer();
        renderer.link = function (href, title, text) {
            if (noLinks || !/^https?:\/\//i.test(href)) return text;
            return '<a href="' + href.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;') + '" target="_blank" rel="noopener noreferrer">' + text + '</a>';
        };
        renderer.image = function (href, title, text) { return text; };
        return renderer;
    }

    function inlineMarkdown(parent, text, noLinks) {
        parent.innerHTML = marked.inlineLexer(text, {}, {renderer: markdownRenderer(noLinks), sanitize: true, gfm: true, breaks: false});
    }

    function markdown(text) {
        var container = element('div', 'markdown');
        container.innerHTML = marked(text, {renderer: markdownRenderer(false), sanitize: true, gfm: true, tables: true});
        return container;
    }

    function showProgress(text) {
        var indicator = messages.querySelector('.message.assistant .activity');
        status.textContent = text;
        if (indicator) indicator.textContent = text;
    }

    function showMessages(items) {
        var i, box, avatar, body, welcome, cards, button;
        currentItems = items;
        messages.textContent = '';
        if (!items.length) {
            welcome = element('div', 'welcome');
            box = element('div', 'welcome-icon');
            box.appendChild(mark('mark-image'));
            welcome.appendChild(box);
            welcome.appendChild(element('div', 'eyebrow', 'IL TUO ASSISTENTE PERSONALE'));
            welcome.appendChild(element('h1', '', 'Come posso aiutarti?'));
            welcome.appendChild(element('p', 'intro', 'Uno spazio per le tue idee, le tue domande e tutto quello che vuoi scoprire.'));
            cards = element('div', 'suggestions');
            var first = Math.floor(Math.random() * suggestions.length);
            var second = Math.floor(Math.random() * (suggestions.length - 1));
            if (second >= first) second += 1;
            var addSuggestion = function (text) {
                var suggestion = element('button', 'suggestion', text);
                suggestion.type = 'button';
                suggestion.onclick = function () {
                    if (busy) return;
                    input.value = text;
                    document.getElementById('chat-form').onsubmit({preventDefault: function () {}});
                };
                cards.appendChild(suggestion);
            };
            addSuggestion(suggestions[first]);
            addSuggestion(suggestions[second]);
            welcome.appendChild(cards);
            messages.appendChild(welcome);
            return;
        }
        body = element('div', 'conversation');
        for (i = 0; i < items.length; i += 1) {
            box = element('div', 'message ' + (items[i].role === 'user' ? 'user' : 'assistant'));
            avatar = element('span', 'avatar', items[i].role === 'user' ? 'TU' : '');
            if (items[i].role !== 'user') avatar.appendChild(mark('mark-image'));
            box.appendChild(avatar);
            box.appendChild(element('strong', '', items[i].role === 'user' ? 'Tu' : 'Assistente'));
            box.appendChild(markdown(items[i].content));
            if (busy && i === items.length - 1 && items[i].role === 'assistant') {
                box.appendChild(element('div', 'activity', status.textContent));
            }
            body.appendChild(box);
        }
        messages.appendChild(body);
        messages.scrollTop = messages.scrollHeight;
    }

    function renderChats() {
        var i, button, icon, row, remove;
        chats.textContent = '';
        if (!list.length) chats.appendChild(element('p', 'empty-list', 'Le tue conversazioni appariranno qui.'));
        for (i = 0; i < list.length; i += 1) {
            row = element('div', 'chat-row' + (String(list[i].id) === String(active) ? ' active' : ''));
            button = element('button', 'chat-item');
            button.type = 'button';
            button.setAttribute('data-id', list[i].id);
            icon = element('span', 'chat-symbol', '▤');
            button.appendChild(icon);
            inlineMarkdown(button, list[i].title, true);
            button.onclick = function () {
                if (busy) return;
                active = this.getAttribute('data-id');
                sidebar.className = 'sidebar';
                updateMenu();
                status.textContent = '';
                renderChats();
                loadMessages();
            };
            remove = element('button', 'delete-chat', '×');
            remove.type = 'button';
            remove.setAttribute('data-id', list[i].id);
            remove.setAttribute('aria-label', 'Elimina conversazione ' + list[i].title);
            remove.onclick = function () {
                var id = this.getAttribute('data-id');
                if (busy || !window.confirm('Eliminare questa conversazione?')) return;
                busy = true;
                request('DELETE', '/api/chats/' + id, null, function (error) {
                    busy = false;
                    if (error) { status.className = 'status error'; status.textContent = error; return; }
                    if (String(active) === String(id)) { active = null; loadVersion += 1; showMessages([]); }
                    status.textContent = '';
                    loadChats();
                });
            };
            row.appendChild(button);
            row.appendChild(remove);
            chats.appendChild(row);
        }
    }

    function loadMessages() {
        var chat = active, version = ++loadVersion;
        if (!chat) { showMessages([]); return; }
        request('GET', '/api/chats/' + chat + '/messages', null, function (error, data) {
            if (version !== loadVersion || String(chat) !== String(active)) return;
            if (error) { status.className = 'status error'; status.textContent = error; return; }
            showMessages(data);
        });
    }

    function loadChats() {
        request('GET', '/api/chats', null, function (error, data) {
            if (error) { status.className = 'status error'; status.textContent = error; return; }
            list = data;
            renderChats();
        });
    }

    menu.onclick = function () {
        if (window.innerWidth <= 700) {
            sidebar.className = sidebar.className === 'sidebar' ? 'sidebar open' : 'sidebar';
        } else {
            app.className = app.className === 'app' ? 'app sidebar-closed' : 'app';
        }
        updateMenu();
    };
    document.getElementById('new-chat').onclick = function () {
        if (busy) return;
        active = null;
        loadVersion += 1;
        sidebar.className = 'sidebar';
        updateMenu();
        status.textContent = '';
        input.value = '';
        renderChats();
        showMessages([]);
        input.focus();
    };
    input.onkeydown = function (event) {
        event = event || window.event;
        if ((event.keyCode || event.which) === 13 && !event.shiftKey && !event.isComposing && event.keyCode !== 229) {
            event.preventDefault();
            document.getElementById('chat-form').onsubmit(event);
        }
    };
    document.getElementById('chat-form').onsubmit = function (event) {
        var content = input.value, chat = active;
        event.preventDefault();
        if (busy || !content.replace(/\s/g, '')) return;
        busy = true;
        status.className = 'status';
        send.disabled = true;
        input.value = '';
        status.textContent = 'Sto pensando…';
        function sendMessage(id) {
            var xhr = new XMLHttpRequest(), offset = 0, pending = '', answer = '', done = false, failed = false;
            var items = currentItems.slice(0);
            items.push({role: 'user', content: content});
            items.push({role: 'assistant', content: ''});
            showMessages(items);
            function process() {
                var lines, i, event;
                if (xhr.readyState < 3) return;
                pending += xhr.responseText.slice(offset);
                offset = xhr.responseText.length;
                lines = pending.split('\n'); pending = lines.pop();
                for (i = 0; i < lines.length; i += 1) {
                    if (!lines[i]) continue;
                    try { event = JSON.parse(lines[i]); } catch (error) { continue; }
                    if (event.status) showProgress(event.status);
                    if (event.text) { answer += event.text; items[items.length - 1].content = answer; status.textContent = 'Sto scrivendo…'; showMessages(items); }
                    if (event.error) { status.className = 'status error'; status.textContent = event.error; failed = true; }
                    if (event.done) done = true;
                }
            }
            xhr.open('POST', '/api/chats/' + id + '/stream', true);
            xhr.timeout = 120000;
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function () {
                if (xhr.readyState === 3 || xhr.readyState === 4) process();
                if (xhr.readyState !== 4) return;
                if (xhr.status === 401) { window.location.replace('/login.html'); return; }
                busy = false; send.disabled = false;
                if (done && !failed) {
                    status.textContent = '';
                    showMessages(items);
                    loadChats();
                } else {
                    if (!failed) { status.className = 'status error'; status.textContent = 'Connessione interrotta. Riprova.'; }
                    if (!input.value) input.value = content;
                    loadMessages(); loadChats();
                }
            };
            xhr.send(JSON.stringify({content: content}));
        }
        if (chat) { sendMessage(chat); return; }
        request('POST', '/api/chats', {}, function (error, data) {
            if (error) { busy = false; send.disabled = false; if (!input.value) input.value = content; status.className = 'status error'; status.textContent = error; return; }
            if (active === null) { active = data.id; renderChats(); }
            sendMessage(data.id);
        });
    };
    if (typeof marked === 'undefined' || typeof suggestions === 'undefined') {
        window.tabletStartupError('risorse della chat mancanti');
        return;
    }
    window.onresize = updateMenu;
    updateMenu();
    showMessages([]);
    status.textContent = '';
    status.className = 'status';
    loadChats();
}());
