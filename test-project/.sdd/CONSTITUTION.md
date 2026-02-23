# Project Constitution

**Version**: 1.0.0
**Last Updated**: 2026-02-21
**Status**: Active

## Purpose

This document defines the non-negotiable principles and standards that govern the sdd-cli project's development. All code, specifications, and design decisions must align with these principles.

sdd-cli is a Python CLI tool for AI-SDD workflow document management, providing SQLite FTS5-based indexing, full-text search, and dependency visualization for `.sdd/` Markdown documents.

## Principle Hierarchy

```
1. Business Principles (Highest Priority)
   ↓
2. Architecture Principles
   ↓
3. Development Methodology Principles
   ↓
4. Technical Constraints
```

Higher priority principles take precedence over lower priority principles.

---

## 1. Business Principles (Highest Priority)

### B-001: Developer Tool Reliability

**Principle**: CLI tool must produce consistent, predictable results. Users trust sdd-cli to correctly index, search, and visualize their specification documents.

**Scope**: All CLI commands and data processing

**Validation Method**:

- [ ] All commands produce deterministic output for the same input
- [ ] Error messages are clear and actionable
- [ ] No silent data loss or corruption

**Violation Examples**:

- Index command silently skips files without warning
- Search returns inconsistent results for the same query

**Compliant Examples**:

- Clear error messages when files cannot be parsed
- Deterministic ordering of search results

---

### B-002: Backward Compatibility

**Principle**: Maintain backward compatibility for CLI interfaces and data formats. Breaking changes require major version bumps.

**Scope**: CLI arguments, output formats, database schema

**Validation Method**:

- [ ] CLI argument changes are backward compatible
- [ ] Database schema changes include migration support
- [ ] Output format changes are documented

**Violation Examples**:

- Renaming CLI subcommands without deprecation period
- Changing database schema without migration

**Compliant Examples**:

- Adding new optional arguments while keeping existing ones
- Versioned database schema with migration support

---

## 2. Architecture Principles

### A-001: Library-First

**Principle**: Leverage existing libraries whenever possible and avoid reinventing the wheel

**Scope**: All implementations

**Validation Method**:

- [ ] Did you research existing libraries before implementing from scratch?
- [ ] Is there a clear reason for custom implementation?

**Violation Examples**:

- Custom YAML/frontmatter parser instead of using python-frontmatter
- Custom CLI argument parsing instead of using Click

**Compliant Examples**:

- Using Click for CLI framework
- Using python-frontmatter for Markdown metadata parsing
- Using SQLite FTS5 for full-text search

---

### A-002: Modular Pipeline Architecture

**Principle**: Processing pipeline follows clear stages: Scan → Parse → Index → Query. Each stage is independently testable.

**Scope**: All data processing modules

**Validation Method**:

- [ ] Each pipeline stage has a single responsibility
- [ ] Stages communicate through well-defined types (TypedDict)
- [ ] Each stage can be tested independently without file system dependencies

**Violation Examples**:

- Scanner module directly writes to database
- Parser depends on database schema

**Compliant Examples**:

- Scanner produces `ScanResult`, Parser produces `ParsedDocument`, DB consumes both
- Each module testable with in-memory data

---

## 3. Development Methodology Principles

### D-001: Test-First

**Principle**: Write tests before implementation (TDD)

**Scope**: All core features

**Validation Method**:

- [ ] Test cases created before implementation
- [ ] Test coverage > 80%
- [ ] Follows flow of writing failing tests first, then making them pass with implementation

**Violation Examples**:

- Adding tests after implementation is complete
- Merging without tests

**Compliant Examples**:

- Follow Red → Green → Refactor cycle
- Test case creation → Implementation → Refactoring

---

### D-002: Specification-Driven

**Principle**: Never implement without specifications

**Scope**: All new features and changes

**Validation Method**:

- [ ] `*_spec.md` exists
- [ ] `*_design.md` exists
- [ ] Specifications are up-to-date (updated before implementation)

**Violation Examples**:

- Starting implementation based only on verbal instructions
- Implementing with outdated specifications

**Compliant Examples**:

- Follow Specify → Plan → Tasks → Implement flow
- Manage specifications as Single Source of Truth

---

## 4. Technical Constraints

### T-001: Python 3.9+ Compatibility

**Principle**: All code must be compatible with Python 3.9 through 3.13. Use future annotations and compatibility shims where needed.

**Scope**: All source code

**Validation Method**:

- [ ] No Python 3.10+ syntax used without fallback (e.g., `match` statement, `X | Y` union types)
- [ ] `from __future__ import annotations` used where appropriate
- [ ] CI matrix tests against Python 3.9, 3.11, and 3.13

**Violation Examples**:

- Using `str | None` instead of `Optional[str]`
- Using `match` statement without Python 3.9 alternative

**Compliant Examples**:

- Using `Union[str, None]` or `Optional[str]` for type hints
- Using `importlib.resources` with compatibility handling

---

### T-002: Type Safety with TypedDict

**Principle**: All data structures flowing through the pipeline are defined as TypedDict in `types.py`. No ad-hoc dictionaries for core data.

**Scope**: All data processing code

**Validation Method**:

- [ ] All pipeline data structures defined in `types.py`
- [ ] mypy passes with `check_untyped_defs = true`
- [ ] No untyped dictionary access in core modules

**Violation Examples**:

- Using `dict[str, Any]` for document records
- Accessing dictionary keys without type definition

**Compliant Examples**:

- `DocumentInfo`, `ParsedDocument`, `DocumentRecord` TypedDict definitions
- Type-checked pipeline: `ScanResult` → `ParsedDocument` → `DocumentRecord`

---

### T-003: Static Methods for Stateless Operations

**Principle**: Parser and utility functions that don't maintain state should be static methods or module-level functions.

**Scope**: Parser, utility modules

**Validation Method**:

- [ ] Parser methods are static (no instance state)
- [ ] No unnecessary class instantiation for stateless operations

**Violation Examples**:

- Creating parser instance just to call a method
- Storing state in parser class that could be passed as arguments

**Compliant Examples**:

- `DocumentParser.parse()` as static method
- Pure functions that take input and return output

---

## Development Standards

### Code Quality

| Standard        | Requirement                | Tool          | Enforcement     |
|:----------------|:---------------------------|:--------------|:----------------|
| **Linting**     | Zero errors, zero warnings | Ruff          | CI/CD           |
| **Type Safety** | check_untyped_defs = true  | mypy          | CI/CD           |
| **Formatting**  | Consistent style           | Ruff format   | CI/CD           |
| **Line Length**  | ≤ 120 characters           | Ruff          | Pre-commit      |

### Testing

| Standard              | Requirement                      | Enforcement          |
|:----------------------|:---------------------------------|:---------------------|
| **Unit Coverage**     | ≥80% line coverage               | CI/CD gate           |
| **Cross-Platform**    | Ubuntu + macOS                   | CI matrix            |
| **Multi-Version**     | Python 3.9, 3.11, 3.13          | CI matrix            |
| **Helper Separation** | Helpers in `tests/helpers.py`    | Code review          |

## Decision-Making Framework

When facing technical trade-offs, prioritize in this order:

1. **Correctness** - Does it meet specifications?
2. **Compatibility** - Does it work on Python 3.9-3.13?
3. **Simplicity** - Is it the simplest solution?
4. **Testability** - Can it be easily tested?
5. **Performance** - Is it fast enough?
6. **Maintainability** - Can we maintain it?

**Tiebreaker**: Choose option that's easier to change later.

## Quality Gates

### Pre-Commit

- [ ] Ruff check passes
- [ ] Ruff format check passes
- [ ] Tests pass locally

### Pre-PR

- [ ] All tests pass
- [ ] Coverage ≥ 80%
- [ ] mypy passes
- [ ] Spec consistency verified (`/check-spec`)

### Pre-Merge

- [ ] CI/CD pipeline green (Ubuntu + macOS, Python 3.9/3.11/3.13)
- [ ] Code review approved
- [ ] No merge conflicts

## Version History

### v1.0.0 (2026-02-21)

**Initial constitution established**

- B-001: Developer Tool Reliability
- B-002: Backward Compatibility
- A-001: Library-First
- A-002: Modular Pipeline Architecture
- D-001: Test-First
- D-002: Specification-Driven
- T-001: Python 3.9+ Compatibility
- T-002: Type Safety with TypedDict
- T-003: Static Methods for Stateless Operations

---

*This constitution is a living document. It should evolve with the team's learning and the project's needs.*
