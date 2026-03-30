---
name: clean-code
description: >
  Use when writing, fixing, editing, reviewing, refactoring, or debugging any code (Python, JavaScript, TypeScript, Java, Go, Rust, etc.).
  Enforces Robert C. Martin's Clean Code principles — naming, functions, comments, DRY, tests, and the Boy Scout Rule.
  Trigger this skill whenever the user mentions code quality, refactoring, code review, clean code, code smells, technical debt,
  naming conventions, function design, test quality, or asks to "clean up" / "improve" / "review" any code.
  Also trigger when generating new code — all generated code should follow these principles by default.
---

# Clean Code — Unified Skill

> "Always check a module in cleaner than when you checked it out." — Robert C. Martin

This skill enforces the complete Clean Code catalog. It combines naming, functions, comments, general principles, tests, and the Boy Scout Rule into a single reference.

For detailed examples and deeper explanations per category, read the corresponding file in `references/`:
- `references/names.md` — Naming rules N1–N7 with examples
- `references/functions.md` — Function rules F1–F4 with examples
- `references/comments.md` — Comment rules C1–C5 with examples
- `references/general.md` — General principles G1–G36 with examples
- `references/tests.md` — Test rules T1–T9 with F.I.R.S.T. principles
- `references/anti-patterns.md` — Common anti-patterns and fixes

---

## The Boy Scout Rule

Every time you touch code, leave it **a little better** than you found it. Not perfect — just better.

**Quick wins** (do immediately): rename a bad variable, delete a redundant comment, remove dead code, replace a magic number, extract a deeply nested block.

**Deeper improvements** (when time allows): split multi-responsibility functions, remove duplication, add missing boundary tests, improve abstractions.

---

## Core Rules — Quick Reference

### Names (N1–N7)

| Rule | Principle | Bad → Good |
|------|-----------|------------|
| N1 | Descriptive names | `d = 86400` → `SECONDS_PER_DAY = 86400` |
| N2 | Right abstraction level | `get_dict_of_user_ids_to_names()` → `get_user_directory()` |
| N3 | Standard nomenclature | Use domain terms and pattern names |
| N4 | Unambiguous | `rename(old, new)` → `rename_file(old_path, new_path)` |
| N5 | Length matches scope | Short for loops, long for globals |
| N6 | No encodings | `lst_users` → `users` |
| N7 | Describe side effects | `get_config()` → `get_or_create_config()` |

**Key insight:** If a name requires a comment to explain what it means, the name doesn't reveal its intent. Rename it.

### Functions (F1–F4)

| Rule | Principle |
|------|-----------|
| F1 | **Maximum 3 arguments.** More means the function does too much — group into a data structure. |
| F2 | **No output arguments.** Don't mutate inputs as side effects — return new values instead. |
| F3 | **No flag arguments.** A boolean parameter means the function does two things — split it. |
| F4 | **Delete dead functions.** If it's not called, delete it. Git remembers. |

**Key insight:** Functions should do one thing (G30). If you can extract another function from it with a meaningful name, it does more than one thing.

### Comments (C1–C5)

| Rule | Principle |
|------|-----------|
| C1 | **No metadata.** Use Git for author, date, ticket numbers. |
| C2 | **Delete obsolete comments** immediately. Stale comments mislead. |
| C3 | **No redundant comments.** Don't explain what the code already says. |
| C4 | **Write well** if you must write a comment. Be brief, precise, grammatical. |
| C5 | **Never commit commented-out code.** Delete it. Git preserves history. |

**Key insight:** The best comment is the code itself. If you need a comment to explain *what* code does, refactor the code first. Comments should explain *why*, not *what*.

### General Principles (G1–G36 highlights)

| Rule | Principle |
|------|-----------|
| G3 | Handle boundary conditions explicitly |
| G5 | **DRY** — every piece of knowledge has one authoritative source |
| G9 | Delete dead code |
| G10 | Variables close to usage |
| G16 | No obscured intent — be clear, not clever |
| G23 | Prefer polymorphism to if/else chains |
| G25 | Named constants, not magic numbers |
| G28 | Encapsulate conditionals into well-named functions |
| G29 | Avoid negative conditionals (`if not is_invalid` → `if is_valid`) |
| G30 | Functions do one thing |
| G34 | One abstraction level per function |
| G36 | Law of Demeter — avoid `obj.a.b.c.value` train wrecks |

### Tests (T1–T9)

| Rule | Principle |
|------|-----------|
| T1 | Test everything that could break |
| T3 | Don't skip trivial tests — they document behavior |
| T5 | **Test boundary conditions** — bugs cluster at boundaries |
| T6 | Exhaustively test near bugs — bugs cluster |
| T9 | Tests must be fast (< 100ms for unit tests) |

**F.I.R.S.T.:** Fast, Independent, Repeatable, Self-Validating, Timely.

**One concept per test.** Don't test creation, validation, and activation in the same test function.

### Environment (E1–E2)

| Rule | Principle |
|------|-----------|
| E1 | One command to build |
| E2 | One command to test |

---

## Language-Specific Adaptations

### Python

| Rule | Principle |
|------|-----------|
| P1 | No wildcard imports (`from x import *`) — explicit imports per PEP 8 |
| P2 | Use Enums, not magic string constants |
| P3 | Type hints on all public interfaces |
| — | Follow PEP 8 (G24) |
| — | Use dataclasses / Pydantic for structured data |
| — | Prefer list comprehensions over manual loops when readable |
| — | Use `pathlib.Path` over string manipulation for file paths |

### JavaScript / TypeScript

| Rule | Principle |
|------|-----------|
| J1 | Use `const` by default, `let` when mutation is needed, never `var` |
| J2 | Use TypeScript types/interfaces instead of `any` |
| J3 | Prefer `===` over `==` |
| — | Use destructuring for clean parameter handling |
| — | Prefer `async/await` over raw Promises/callbacks |
| — | Use template literals over string concatenation |

### Go

| Rule | Principle |
|------|-----------|
| Go1 | Handle errors explicitly — never ignore returned errors |
| Go2 | Use meaningful receiver names (not single letters except for simple types) |
| Go3 | Keep interfaces small — prefer single-method interfaces |
| — | Use `context.Context` for cancellation and deadlines |

### Java

| Rule | Principle |
|------|-----------|
| J1 | Avoid wildcard imports |
| J2 | Don't inherit constants — use static imports or enums |
| J3 | Use enums over magic constants |

---

## Anti-Patterns — Don't → Do

| ❌ Don't | ✅ Do |
|----------|-------|
| Comment every line | Write self-documenting code, delete obvious comments |
| Helper function for a one-liner | Inline it |
| `from x import *` | Explicit imports |
| Magic number `86400` | `SECONDS_PER_DAY = 86400` |
| `process(data, True)` | `process_with_tax(data)` |
| Deep nesting (3+ levels) | Guard clauses, early returns |
| `obj.a.b.c.value` | `obj.get_value()` |
| 100+ line function | Split by responsibility |
| `# increment i` next to `i += 1` | Delete the comment |
| `@skip("fix later")` on tests | Fix the test or delete it |
| Testing 5 things in one test | One concept per test function |
| Returning `None` to signal errors | Raise exceptions with clear messages |

---

## AI Behavior Rules

### When generating new code:
1. Apply all rules automatically — don't wait to be asked
2. Use descriptive names (N1), keep functions small and focused (G30, F1)
3. No magic numbers (G25), no dead code (G9), no redundant comments (C3)
4. Add type hints on public interfaces (P3/J2)
5. Handle boundary conditions (G3)

### When reviewing or refactoring code:
1. **Identify violations by rule number** (e.g., "G5 violation: duplicated tax calculation logic")
2. Prioritize: correctness first, then clarity, then conciseness
3. Suggest incremental improvements, not complete rewrites
4. Apply the Boy Scout Rule — fix at least one thing beyond the requested change

### When fixing bugs:
1. Fix the bug first
2. Look for at least one Boy Scout improvement
3. Write tests for the bug and nearby boundary conditions (T5, T6)
4. Report what was cleaned: "Also cleaned up: renamed `x` to `results` for clarity (N1)"

### Reporting format:
When you make clean code improvements, briefly note them:
```
✅ Fixed: extracted magic number to SECONDS_PER_DAY (G25)
✅ Fixed: split process() into process_items() and apply_tax() (G30)
✅ Fixed: deleted obsolete comment on line 42 (C2)
```

---

## Enforcement Checklist

Use this checklist when reviewing any code:

- [ ] Names are descriptive and reveal intent (N1)
- [ ] Functions have ≤ 3 arguments (F1)
- [ ] Functions do one thing (G30)
- [ ] No flag arguments (F3)
- [ ] No duplication (G5)
- [ ] No magic numbers (G25)
- [ ] No obscured intent (G16)
- [ ] No commented-out code (C5)
- [ ] No redundant comments (C3)
- [ ] No dead code or dead functions (G9, F4)
- [ ] Boundary conditions handled (G3)
- [ ] No Law of Demeter violations (G36)
- [ ] Conditionals encapsulated (G28)
- [ ] No negative conditionals (G29)
- [ ] Tests cover boundaries (T5)
- [ ] Tests are fast and independent (T9, F.I.R.S.T.)
- [ ] One concept per test (T1)
- [ ] Type hints on public interfaces (P3/J2)
- [ ] One command to build, one to test (E1, E2)
