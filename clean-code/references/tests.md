# Clean Tests — Detailed Reference (T1–T9)

## T1: Insufficient Tests

Test everything that could possibly break. Use coverage tools as a guide, not a goal.

```python
# Bad — only tests happy path
def test_divide():
    assert divide(10, 2) == 5

# Good — tests edge cases too
def test_divide_normal():
    assert divide(10, 2) == 5

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

def test_divide_negative():
    assert divide(-10, 2) == -5
```

## T2: Use a Coverage Tool

Coverage tools report gaps in your testing strategy. Don't ignore them.

```bash
# Python
pytest --cov=myproject --cov-report=term-missing

# JavaScript
npx jest --coverage

# Go
go test -cover ./...
```

Aim for meaningful coverage, not 100%. Untested code paths often reveal design problems.

## T3: Don't Skip Trivial Tests

Trivial tests document behavior and catch regressions. They cost almost nothing to write.

```python
# Worth having — documents expected behavior
def test_user_default_role():
    user = User(name="Alice")
    assert user.role == "member"
```

## T4: An Ignored Test Is a Question About an Ambiguity

Don't use `@skip` to hide problems. Either fix the test or delete it.

```python
# Bad — hiding a problem
@pytest.mark.skip(reason="flaky, fix later")
def test_async_operation():
    ...

# Good — documents WHY it's skipped with actionable info
@pytest.mark.skip(reason="Requires Redis; see CONTRIBUTING.md for local setup")
def test_cache_invalidation():
    ...
```

## T5: Test Boundary Conditions

Bugs congregate at boundaries. Test them explicitly.

```python
def test_pagination_boundaries():
    items = list(range(100))

    assert paginate(items, page=1, size=10) == items[0:10]     # First page
    assert paginate(items, page=10, size=10) == items[90:100]   # Last page
    assert paginate(items, page=11, size=10) == []              # Beyond last page
    assert paginate([], page=1, size=10) == []                  # Empty list

    with pytest.raises(ValueError):
        paginate(items, page=0, size=10)  # Invalid page
```

## T6: Exhaustively Test Near Bugs

When you find a bug, write tests for all similar cases. Bugs cluster.

```python
# Found bug: off-by-one in date calculation
# Now test ALL date boundaries
def test_month_boundaries():
    assert last_day_of_month(2024, 1) == 31   # January
    assert last_day_of_month(2024, 2) == 29   # Leap year February
    assert last_day_of_month(2023, 2) == 28   # Non-leap February
    assert last_day_of_month(2024, 4) == 30   # 30-day month
    assert last_day_of_month(2024, 12) == 31  # December
```

## T7: Patterns of Failure Are Revealing

When tests fail, look for patterns. If all async tests fail intermittently, the problem isn't the tests — it's the async handling.

## T8: Test Coverage Patterns Can Be Revealing

Look at which code paths are untested. If you can't easily test a function, it probably does too much — refactor for testability.

## T9: Tests Should Be Fast

Slow tests don't get run. Keep unit tests under 100ms each.

```python
# Bad — hits real database
def test_user_creation():
    db = connect_to_database()  # Slow!
    user = db.create_user("Alice")
    assert user.name == "Alice"

# Good — uses mock or in-memory
def test_user_creation():
    db = InMemoryDatabase()
    user = db.create_user("Alice")
    assert user.name == "Alice"
```

## F.I.R.S.T. Principles

| Principle | Meaning |
|-----------|---------|
| **Fast** | Tests run quickly (< 100ms each for unit tests) |
| **Independent** | Tests don't depend on each other or run order |
| **Repeatable** | Same result every time, any environment |
| **Self-Validating** | Pass or fail — no manual inspection needed |
| **Timely** | Written before or with the code, not months later |

## One Concept Per Test

```python
# Bad — testing multiple concepts
def test_user():
    user = User("Alice", "alice@example.com")
    assert user.name == "Alice"
    assert user.email == "alice@example.com"
    assert user.is_valid()
    user.activate()
    assert user.is_active

# Good — one concept each
def test_user_stores_name():
    assert User("Alice", "a@b.com").name == "Alice"

def test_user_stores_email():
    assert User("Alice", "a@b.com").email == "a@b.com"

def test_new_user_is_valid():
    assert User("Alice", "a@b.com").is_valid()

def test_user_can_be_activated():
    user = User("Alice", "a@b.com")
    user.activate()
    assert user.is_active
```

## Test Naming Convention

Test names should describe the scenario, not the implementation:

```python
# Bad
def test_calculate_1():
def test_calculate_2():

# Good
def test_calculate_total_with_tax():
def test_calculate_total_without_items_raises_error():
def test_calculate_total_with_discount_applied_last():
```
