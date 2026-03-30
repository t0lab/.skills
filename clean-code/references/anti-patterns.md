# Anti-Patterns — Comprehensive Don't → Do Guide

## Naming Anti-Patterns

| ❌ Anti-Pattern | ✅ Clean Alternative | Rule |
|----------------|---------------------|------|
| Single-letter names at module scope: `d = 86400` | `SECONDS_PER_DAY = 86400` | N1 |
| Hungarian notation: `str_name`, `lst_users` | `name`, `users` | N6 |
| Implementation-leaking names: `get_dict_of_ids()` | `get_user_directory()` | N2 |
| Misleading names: `get_config()` that also creates files | `get_or_create_config()` | N7 |
| Abbreviated names: `calc_amt()` | `calculate_amount()` | N1 |
| Names that differ by number: `data1`, `data2` | `raw_data`, `processed_data` | N4 |

## Function Anti-Patterns

| ❌ Anti-Pattern | ✅ Clean Alternative | Rule |
|----------------|---------------------|------|
| 5+ parameters | Use a dataclass / options object | F1 |
| Boolean flag parameter: `render(is_test=True)` | `render_test_page()` | F3 |
| Mutating input arguments | Return new values | F2 |
| Function > 30 lines | Extract sub-functions | G30 |
| Deep nesting (3+ levels) | Guard clauses, early returns | G34 |
| Function does multiple things | Split by responsibility | G30 |

## Comment Anti-Patterns

| ❌ Anti-Pattern | ✅ Clean Alternative | Rule |
|----------------|---------------------|------|
| `i += 1  # increment i` | Delete the comment | C3 |
| `# Author: John, Date: 2024-01-15` | Use Git | C1 |
| Commented-out code blocks | Delete. Git remembers. | C5 |
| Stale comments describing old behavior | Delete or update | C2 |
| Journal comments at top of file | Use Git log | C1 |

## General Anti-Patterns

| ❌ Anti-Pattern | ✅ Clean Alternative | Rule |
|----------------|---------------------|------|
| Copy-paste code blocks | Extract shared function | G5 |
| Magic number: `if age > 18` | `LEGAL_DRINKING_AGE = 18` | G25 |
| Train wreck: `obj.a.b.c.value` | `obj.get_value()` | G36 |
| Growing if/elif chain | Polymorphism or strategy pattern | G23 |
| `if not is_not_valid` | `if is_valid` | G29 |
| Mixed abstraction levels in one function | Separate high/low level | G34 |
| Config values buried in logic | Extract to config at top | G35 |
| Catch-all exception: `except Exception` | Catch specific exceptions | G26 |

## Test Anti-Patterns

| ❌ Anti-Pattern | ✅ Clean Alternative | Rule |
|----------------|---------------------|------|
| Only testing happy path | Test boundaries and errors too | T1, T5 |
| Testing 5 things in one test | One concept per test | T1 |
| `@skip("fix later")` without action plan | Fix it or delete it | T4 |
| Tests hitting real database | Use mocks / in-memory | T9 |
| Tests depending on run order | Make each test independent | F.I.R.S.T. |
| `test_1`, `test_2` naming | Descriptive scenario names | N1 |
| Returning None to signal errors | Raise exceptions | G26 |
| Manual inspection to verify test result | Assert with clear messages | F.I.R.S.T. |

## Code Smell Detection Guide

When you see any of these, it's a signal to refactor:

**Smell: Long function** → Extract methods by responsibility (G30)
**Smell: Long parameter list** → Introduce parameter object (F1)
**Smell: Duplicate code** → Extract shared function (G5)
**Smell: Conditional complexity** → Use polymorphism (G23) or extract conditions (G28)
**Smell: Feature envy** → Move method to the class it envies (G14)
**Smell: Data clump** → Group related data into a class (F1)
**Smell: Primitive obsession** → Replace primitives with value objects
**Smell: Shotgun surgery** → Consolidate scattered changes (G5)
**Smell: Comments explaining "what"** → Rename the code to be self-documenting (N1, C3)
