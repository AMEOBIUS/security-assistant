// VULNERABLE:
// File file = new File("/var/www/uploads/" + filename);

// SECURE (Path Normalization and Validation):
import java.nio.file.Path;
import java.nio.file.Paths;

Path basePath = Paths.get("/var/www/uploads").toRealPath();
Path requestedPath = basePath.resolve(filename).normalize();

// Ensure the resolved path is still within base directory
if (!requestedPath.startsWith(basePath)) {
    throw new SecurityException("Path traversal attempt detected");
}

File file = requestedPath.toFile();
