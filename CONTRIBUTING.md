# Contributing to OConsent

## Development Process
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-oconsent-feature`)
3. Install development dependencies (`pip install -r requirements_dev.txt`)
4. Install pre-commit hooks (`pre-commit install`)
5. Make your changes
6. Run tests (`tox`)
7. Commit your changes (`git commit -m 'Add amazing oconsent feature'`)
8. Push to the branch (`git push origin feature/amazing-oconsent-feature`)
9. Open a Pull Request

## Code Style
- Follow PEP 8 guidelines
- Use Black for code formatting
- Sort imports with isort
- Add docstrings for all public functions

## Testing
- Write unit tests for new features
- Maintain test coverage above 90%
- Run the full test suite before submitting PR