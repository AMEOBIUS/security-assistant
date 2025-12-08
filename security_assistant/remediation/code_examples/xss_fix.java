// VULNERABLE:
// response.getWriter().write("<div>" + userInput + "</div>");

// SECURE (HTML Escaping with OWASP Java Encoder):
import org.owasp.encoder.Encode;

response.getWriter().write("<div>" + Encode.forHtml(userInput) + "</div>");

// Alternative with Spring Framework:
import org.springframework.web.util.HtmlUtils;

response.getWriter().write("<div>" + HtmlUtils.htmlEscape(userInput) + "</div>");
