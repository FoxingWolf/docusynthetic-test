# Contributing to DocuSynthetic

Thank you for your interest in contributing to DocuSynthetic!

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip

### Getting Started

1. Fork and clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/docusynthetic-test.git
cd docusynthetic-test
```

2. Install in development mode:
```bash
pip install -e '.[dev]'
```

3. Install Playwright browsers:
```bash
playwright install chromium
```

### Running Tests

Run all tests:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest tests/ --cov=docusynthetic --cov-report=html
```

### Code Quality

Format code with Black:
```bash
black docusynthetic/
```

Lint with Ruff:
```bash
ruff check docusynthetic/
```

Type check with mypy:
```bash
mypy docusynthetic/
```

### Making Changes

1. Create a new branch for your feature:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and add tests

3. Run tests and linters

4. Commit your changes:
```bash
git commit -m "Add your feature description"
```

5. Push to your fork and create a pull request

## Pull Request Guidelines

- Write clear, descriptive commit messages
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass
- Follow the existing code style

## Reporting Issues

When reporting issues, please include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Any error messages

## Questions?

Feel free to open an issue for any questions or discussions.
