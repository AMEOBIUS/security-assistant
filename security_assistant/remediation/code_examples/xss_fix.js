// VULNERABLE:
// element.innerHTML = "Hello " + userInput;

// SECURE:
// Use textContent for plain text
element.textContent = "Hello " + userInput;

// OR Use a library like DOMPurify
// import DOMPurify from 'dompurify';
// element.innerHTML = DOMPurify.sanitize("Hello " + userInput);

// OR In React:
// <div>{userInput}</div>  // Auto-escaped
// AVOID: <div dangerouslySetInnerHTML={{__html: userInput}} />
