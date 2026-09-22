# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in MarkdownURL, please report it privately.

**Do NOT open a public issue.** Instead, contact the maintainer directly:

- **Email:** sema19689@gmail.com

### What to include

1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact

### What to expect

- Acknowledgment within 48 hours
- Status update within 1 week
- Public disclosure after fix (with your permission)

## Security Measures

MarkdownURL implements the following security practices:

- HTTP requests use timeouts (default 10s)
- Retry logic with exponential backoff
- Content-Type validation for image downloads
- URL encoding/decoding with proper error handling
- No `eval()`/`exec()` usage
- No `subprocess` calls
- No hardcoded credentials or API keys
