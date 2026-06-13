## ADDED Requirements

### Requirement: All source code is written in English

All comments, docstrings, log messages, print statements, and identifier names in Python source files SHALL be in English. Spanish-language text in these positions is a violation of the project language standard.

#### Scenario: Comment in a Python file

- **WHEN** a developer reads any `.py` file in the repo
- **THEN** all `#` comments and docstrings are in English

#### Scenario: Log and print output

- **WHEN** the application or any script emits a log line or print statement
- **THEN** the message is in English

### Requirement: UI strings in templates remain in Spanish

All static text in `templates/*.html` SHALL remain in Spanish. The app serves an Argentine user base; translating UI copy to English is out of scope.

#### Scenario: Dashboard page unchanged

- **WHEN** a user loads the dashboard (`/`)
- **THEN** all labels, section titles, and button text are still in Spanish

### Requirement: Spanish product-matching keywords are preserved

Spanish keyword lists inside `CATEGORIAS` in `normalizer.py` SHALL remain in Spanish, because they are matched against Spanish-language product names scraped from Argentine supermarkets. Translating them would break category detection.

#### Scenario: Category detection still works after translation pass

- **WHEN** `detectar_categoria("leche entera la serenísima 1lt")` is called
- **THEN** it returns `"lacteos"` (unchanged behavior)
