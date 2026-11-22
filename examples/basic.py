from parse_html5 import parse, parse_fragment, render


document = parse('<main><h1>Hello &amp; welcome</h1><img src="photo.jpg" alt="A photo"></main>')
print(document.to_html())

fragment = parse_fragment('<p>one</p><p>two</p>')
print(render(fragment))
