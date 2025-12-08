# VULNERABLE:
# return "<h1>Hello, " + user_input + "</h1>"

# SECURE (using html.escape):
import html

safe_input = html.escape(user_input)
return f"<h1>Hello, {safe_input}</h1>"

# SECURE (using Flask/Jinja2 - automatic):
# {{ user_input }}  <-- Jinja2 escapes by default
