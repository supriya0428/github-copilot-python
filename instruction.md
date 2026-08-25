# Project Guidance for GitHub Copilot

Use these guidelines when assisting with this Udacity GitHub Copilot Python Sudoku project.

## General Development Standards

- Use modern, readable Python and Flask practices that are appropriate for the project's existing version and structure.
- Keep application logic modular and separated into logical components.
- Prefer small, reusable functions with clear names and single, understandable responsibilities.
- Add type hints where they improve clarity without making the code unnecessarily verbose.
- Preserve existing functionality during refactoring unless a requirement explicitly requests a behavior change.
- Do not introduce dependencies unless they are necessary and justified; prefer the standard library and existing project dependencies.
- Handle errors consistently, provide useful feedback where appropriate, and never silently swallow exceptions.
- Follow PEP 8 and keep code readable, maintainable, and straightforward to review.
- Avoid hard-coded values when a named constant or configuration value is more appropriate.
- Explain unfamiliar or non-obvious implementation decisions with concise documentation or comments when useful.

## Testing and Validation

- Add or update focused tests when modifying existing functionality or adding important new functionality.
- Run the test suite after meaningful code changes and do not knowingly leave failing tests.
- When a change affects multiple layers, validate the relevant backend, frontend, and integration behavior as applicable.
- Prefer tests that verify observable behavior and important edge cases rather than implementation details.

## Sudoku Requirements

- Generated puzzles must be valid Sudoku puzzles and must have exactly one solution.
- Difficulty levels must meaningfully control the number of prefilled cells. Keep the difficulty-to-prefilled-cell policy explicit and easy to adjust.
- Prefilled cells and cells filled by the hint feature must be protected from user modification.
- Solution checking, hints, validation feedback, and puzzle generation must remain consistent with the current puzzle and its solution.

## Application Structure and UI

- Keep frontend behavior, Flask routes, Sudoku logic, and persistence concerns appropriately separated.
- Preserve clear boundaries between request handling, game state, puzzle generation/solving, browser interaction, and score persistence.
- Build responsive and accessible UI behavior that works in both light and dark modes.
- Preserve the project’s expected game behavior, including timer, difficulty selection, hints, solution checking, immediate input feedback, and top-score persistence, unless a requirement says otherwise.
- Use accessible labels, keyboard-friendly interactions, sufficient contrast, and meaningful feedback for user actions.

## Copilot Workflow

- When suggesting a significant change, inspect the existing code, tests, and project structure first rather than assuming how they work.
- Before editing, identify the smallest logical component responsible for the behavior and make the narrowest change that satisfies the requirement.
- Do not blindly implement a requested or generated solution if it conflicts with the project requirements. Point out the conflict and propose a safer alternative.
- Keep implementation choices aligned with the Udacity project rubric and the behavior documented in `README.md`.
- Avoid unrelated refactors, formatting churn, and changes to public behavior that are not required by the task.
