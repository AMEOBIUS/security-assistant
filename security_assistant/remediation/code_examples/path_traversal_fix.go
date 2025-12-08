// VULNERABLE:
// filepath := "/var/www/uploads/" + filename
// data, err := ioutil.ReadFile(filepath)

// SECURE (Path Validation with filepath.Clean):
import (
    "path/filepath"
    "strings"
)

baseDir := "/var/www/uploads"
cleanPath := filepath.Clean(filepath.Join(baseDir, filename))

// Ensure path is within base directory
if !strings.HasPrefix(cleanPath, baseDir) {
    return errors.New("path traversal attempt detected")
}

data, err := ioutil.ReadFile(cleanPath)
