/* Run with node frontend/tests/markdown.test.js. */
var assert = require('assert');
var fs = require('fs');
var vm = require('vm');
var path = require('path');
var root = path.join(__dirname, '..');
var context = {
    marked: require(path.join(root, 'vendor/marked/marked.min.js')),
    katex: require(path.join(root, 'vendor/katex/katex.min.js'))
};
context.window = context;
vm.runInNewContext(fs.readFileSync(path.join(root, 'vendor/prism/prism.min.js'), 'utf8'), context);
vm.runInNewContext(fs.readFileSync(path.join(root, 'js/markdown.js'), 'utf8'), context);
var render = function (text) { return context.tabletMarkdown.render(text, false, false); };
assert.ok(render('$$\\frac{1}{2}$$').indexOf('katex-display') !== -1);
assert.ok(render('\\[x^2\\]').indexOf('katex-display') !== -1);
assert.ok(render('$x$ and \\(y_1\\)').match(/class="katex"/g).length === 2);
assert.ok(render('`$x$`\n\n```tex\n$$x$$\n```').indexOf('katex') === -1);
assert.ok(render('$$x').indexOf('$$x') !== -1);
assert.ok(render('| A | B |\n|---|---|\n| 1 | 2 |\n\n---').indexOf('<table>') !== -1);
assert.ok(render('<img src=x onerror=alert(1)>').indexOf('<img') === -1);
assert.ok(render('```python\nprint(1)\n```').indexOf('token ') !== -1);
assert.ok(render('```unknown\n<tag>\n```').indexOf('&lt;tag&gt;') !== -1);
assert.ok(context.tabletMarkdown.render('```python\nprint(1)\n```', false, false, false).indexOf('token ') === -1);
console.log('Markdown, formule e codice: verifiche superate.');
