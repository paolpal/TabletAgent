/* ES5 Markdown and TeX rendering. Code spans are kept intact before parsing math. */
(function (global) {
    'use strict';

    function renderer(noLinks, highlight) {
        var result = new marked.Renderer();
        var defaultCode = result.code;
        result.code = function (code, language, escaped) {
            var name = (language || '').split(/\s+/)[0].toLowerCase();
            var aliases = {js: 'javascript', ts: 'typescript', py: 'python', sh: 'bash', shell: 'bash', yml: 'yaml', html: 'markup', xml: 'markup'};
            name = aliases[name] || name;
            if (!highlight || !global.Prism || !global.Prism.languages[name] || code.length > 20000) {
                return defaultCode.call(this, code, language, escaped);
            }
            try {
                return '<pre><code class="language-' + name + '">' + global.Prism.highlight(code, global.Prism.languages[name], name) + '</code></pre>\n';
            } catch (error) {
                return defaultCode.call(this, code, language, escaped);
            }
        };
        result.link = function (href, title, text) {
            if (noLinks || !/^https?:\/\//i.test(href)) return text;
            return '<a href="' + href.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;') + '" target="_blank" rel="noopener noreferrer">' + text + '</a>';
        };
        result.image = function (href, title, text) { return text; };
        return result;
    }

    function render(text, inline, noLinks, highlight) {
        var expressions = [];
        var prefix = 'TABLETAGENTMATH';
        var pattern = /(^ {0,3}(`{3,}|~{3,})[^\n]*\n[\s\S]*?^ {0,3}\2[ \t]*(?:\n|$)|^ {4}[^\n]*(?:\n(?: {4}[^\n]*|[ \t]*)|$)*|(`+)[^\n]*?\3|\\\[[\s\S]+?\\\]|\\\([^\n]+?\\\)|\$\$[\s\S]+?\$\$|\$(?!\s|\$)[^\n$]*?[^\s\\$]\$)/gm;
        var options = {renderer: renderer(noLinks, highlight !== false), sanitize: true, gfm: true, tables: true, breaks: false};
        var html;
        text = String(text || '');
        while (text.indexOf(prefix) !== -1) prefix += 'X';
        if (typeof global.katex !== 'undefined') {
            text = text.replace(pattern, function (match, code, fence, ticks, offset, source) {
                var display, tex, rendered, before, slashes = 0;
                if (fence || ticks || /^ {4}/.test(match)) return match;
                before = offset - 1;
                while (before >= 0 && source.charAt(before) === '\\') { slashes += 1; before -= 1; }
                if (slashes % 2) return match;
                display = match.slice(0, 2) === '$$' || match.slice(0, 2) === '\\[';
                tex = match.slice(display || match.charAt(0) === '\\' ? 2 : 1, display || match.charAt(0) === '\\' ? -2 : -1);
                try {
                    rendered = global.katex.renderToString(tex, {displayMode: display, throwOnError: false, trust: false, strict: 'ignore'});
                } catch (error) { return match; }
                expressions.push(rendered);
                return prefix + (expressions.length - 1) + 'END';
            });
        }
        html = inline ? marked.inlineLexer(text, {}, options) : marked(text, options);
        html = html.replace(new RegExp(prefix + '(\\d+)END', 'g'), function (match, index) {
            return expressions[Number(index)] || match;
        });
        return html;
    }
    global.tabletMarkdown = {render: render};
}(window));
