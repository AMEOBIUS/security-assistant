// VULNERABLE:
// cmd := exec.Command("sh", "-c", "ping "+userInput)
// output, err := cmd.Output()

// SECURE (Direct command with arguments):
import (
    "os/exec"
    "regexp"
)

// Validate input
if !regexp.MustCompile(`^[a-zA-Z0-9.-]+$`).MatchString(userInput) {
    return errors.New("invalid hostname")
}

// Use direct command (no shell)
cmd := exec.Command("ping", "-c", "4", userInput)
output, err := cmd.Output()
