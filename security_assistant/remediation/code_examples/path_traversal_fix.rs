// VULNERABLE:
// let path = format!("/var/www/uploads/{}", filename);
// let contents = fs::read_to_string(path)?;

// SECURE (Path Canonicalization and Validation):
use std::path::{Path, PathBuf};
use std::fs;

let base_dir = Path::new("/var/www/uploads").canonicalize()?;
let requested_path = base_dir.join(filename).canonicalize()?;

// Ensure path is within base directory
if !requested_path.starts_with(&base_dir) {
    return Err("Path traversal attempt detected".into());
}

let contents = fs::read_to_string(requested_path)?;
