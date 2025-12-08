// VULNERABLE:
// Runtime.getRuntime().exec("ping " + userInput);

// SECURE (Array-based command with validation):
import java.util.regex.Pattern;

// Validate input
if (!Pattern.matches("^[a-zA-Z0-9.-]+$", userInput)) {
    throw new IllegalArgumentException("Invalid hostname");
}

// Use array form (no shell interpretation)
ProcessBuilder pb = new ProcessBuilder("ping", "-c", "4", userInput);
Process process = pb.start();
