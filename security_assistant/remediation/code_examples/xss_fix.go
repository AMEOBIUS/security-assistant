// VULNERABLE:
// fmt.Fprintf(w, "<div>%s</div>", userInput)

// SECURE (HTML Template with Auto-Escaping):
import "html/template"

tmpl := template.Must(template.New("page").Parse("<div>{{.}}</div>"))
tmpl.Execute(w, userInput) // Automatically escapes HTML
