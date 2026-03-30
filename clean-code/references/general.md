# General Clean Code Principles — Detailed Reference (G1–G36)

## Critical Rules (with examples)

### G3: Handle Boundary Conditions

```python
# Bad — doesn't handle edge cases
def average(numbers):
    return sum(numbers) / len(numbers)

# Good — handles empty list
def average(numbers: list[float]) -> float:
    if not numbers:
        raise ValueError("Cannot average an empty list")
    return sum(numbers) / len(numbers)
```

### G5: DRY (Don't Repeat Yourself)

Every piece of knowledge has one authoritative representation.

```python
# Bad — duplication
tax_rate = 0.0825
ca_total = subtotal * 1.0825
ny_total = subtotal * 1.07

# Good — single source of truth
TAX_RATES = {"CA": 0.0825, "NY": 0.07}
def calculate_total(subtotal: float, state: str) -> float:
    return subtotal * (1 + TAX_RATES[state])
```

### G9: Delete Dead Code

If code isn't executed, delete it. Dead code rots — it confuses readers and never gets updated when surrounding code changes.

### G10: Variables Near Usage

Declare variables close to where they're used. Don't declare everything at the top of a long function.

### G16: No Obscured Intent

Don't be clever. Be clear.

```python
# Bad — what does this do?
return (x & 0x0F) << 4 | (y & 0x0F)

# Good — obvious intent
return pack_nibbles(x, y)
```

### G23: Prefer Polymorphism to If/Else

```python
# Bad — will grow with every new type
def calculate_pay(employee):
    if employee.type == "SALARIED":
        return employee.salary
    elif employee.type == "HOURLY":
        return employee.hours * employee.rate
    elif employee.type == "COMMISSIONED":
        return employee.base + employee.commission

# Good — open/closed principle
class SalariedEmployee:
    def calculate_pay(self) -> float:
        return self.salary

class HourlyEmployee:
    def calculate_pay(self) -> float:
        return self.hours * self.rate
```

### G25: Replace Magic Numbers with Named Constants

```python
# Bad
if elapsed_time > 86400:
    ...

# Good
SECONDS_PER_DAY = 86400
if elapsed_time > SECONDS_PER_DAY:
    ...
```

### G28: Encapsulate Conditionals

```python
# Bad — what does this condition mean?
if user.age >= 18 and user.has_id and not user.is_banned:
    serve_alcohol()

# Good — intention is clear
if user.can_purchase_alcohol():
    serve_alcohol()
```

### G29: Avoid Negative Conditionals

```python
# Bad — double negatives hurt readability
if not is_not_valid:
    ...

# Good
if is_valid:
    ...
```

### G30: Functions Do One Thing

If you can extract another function from it with a meaningful name, the original function does more than one thing.

### G34: One Abstraction Level Per Function

Don't mix high-level orchestration with low-level details in the same function.

```python
# Bad — mixed levels
def process_order(order):
    # High level
    validate(order)
    # Suddenly low level
    conn = psycopg2.connect(host="db.local", port=5432)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO orders ...")

# Good — consistent level
def process_order(order):
    validate(order)
    total = calculate_total(order)
    save_order(order, total)
```

### G36: Law of Demeter (Avoid Train Wrecks)

```python
# Bad — reaching through multiple objects
output_dir = context.options.scratch_dir.absolute_path

# Good — one dot
output_dir = context.get_scratch_dir()
```

## Complete Rule List

| Rule | Principle |
|------|-----------|
| G1 | One language per file |
| G2 | Implement expected behavior (principle of least surprise) |
| G3 | Handle boundary conditions |
| G4 | Don't override safeties (linter disables, type ignores) |
| G5 | DRY — no duplication |
| G6 | Consistent abstraction levels |
| G7 | Base classes don't know about children |
| G8 | Minimize public interface |
| G9 | Delete dead code |
| G10 | Variables near usage |
| G11 | Be consistent (same pattern everywhere) |
| G12 | Remove clutter (unused variables, unreachable code) |
| G13 | No artificial coupling (don't group unrelated things) |
| G14 | No feature envy (method uses another class's data too much) |
| G15 | No selector arguments (similar to F3) |
| G16 | No obscured intent |
| G17 | Code where expected (put things where readers expect them) |
| G18 | Prefer instance methods over static when accessing instance state |
| G19 | Use explanatory variables for complex expressions |
| G20 | Function names say what they do |
| G21 | Understand the algorithm before coding it |
| G22 | Make logical dependencies physical (explicit imports/parameters) |
| G23 | Prefer polymorphism to if/else chains |
| G24 | Follow conventions (PEP 8, ESLint, etc.) |
| G25 | Named constants, not magic numbers |
| G26 | Be precise (don't use float for money, don't ignore race conditions) |
| G27 | Structure over convention (enforce via types, not comments) |
| G28 | Encapsulate conditionals |
| G29 | Avoid negative conditionals |
| G30 | Functions do one thing |
| G31 | Make temporal coupling explicit (if A must run before B, make it obvious) |
| G32 | Don't be arbitrary (every structure decision should have a reason) |
| G33 | Encapsulate boundary conditions (put +1/-1 adjustments in named functions) |
| G34 | One abstraction level per function |
| G35 | Configuration at high levels (not buried in low-level code) |
| G36 | Law of Demeter (no train wrecks) |
