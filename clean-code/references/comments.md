# Clean Comments — Detailed Reference (C1–C5)

## C1: No Inappropriate Information

Comments shouldn't hold metadata. Use Git for author names, change history, ticket numbers, and dates. Comments are for technical notes about code only.

```python
# Bad — metadata belongs in Git
# Author: John Doe
# Date: 2024-01-15
# Ticket: JIRA-1234
# Changed: updated tax rate from 7% to 8.25%
def calculate_tax(amount):
    return amount * 0.0825
```

## C2: Delete Obsolete Comments

If a comment describes code that no longer exists or works differently, delete it immediately. Stale comments become "floating islands of irrelevance and misdirection."

```python
# Bad — comment describes old behavior
def get_users():
    # Returns users sorted by last login date  <-- actually returns by name now
    return db.query(User).order_by(User.name).all()
```

## C3: No Redundant Comments

The code already tells you *what*. Comments should tell you *why*.

```python
# Bad — the code already says this
i += 1  # increment i
user.save()  # save the user
results = []  # initialize empty results list

# Good — explains WHY, not WHAT
i += 1  # compensate for zero-indexing in display
user.save()  # must persist before sending confirmation email
results = []  # accumulator for parallel batch results; merged after all threads complete
```

## C4: Write Comments Well

If a comment is worth writing, write it well. Choose words carefully, use correct grammar, don't ramble or state the obvious. Be brief.

```python
# Bad — rambling and unclear
# This function is used to calculate the thing with the stuff
# and it also handles some edge cases maybe I think

# Good — precise and useful
# Retry with exponential backoff: 1s, 2s, 4s, then fail.
# Required because the upstream API rate-limits at 100 req/min.
```

## C5: Never Commit Commented-Out Code

```python
# Bad — delete this
# def old_calculate_tax(income):
#     return income * 0.15

# Also bad — even "temporary" commented code
# TODO: remove after migration
# for user in legacy_users:
#     migrate(user)
```

Who knows how old it is? Who knows if it's meaningful? Delete it. Git remembers everything.

## When Comments Are Valuable

Comments earn their place when they explain:
- **Why** a non-obvious decision was made
- **Warnings** about consequences ("changing this breaks the API contract")
- **Legal** obligations (license headers)
- **TODO** items with ticket references (sparingly)
- **Clarification** of complex algorithms that can't be simplified further

```python
# Good examples of valuable comments:

# WARNING: Order matters. Tax must be calculated before discount
# because the legal requirement is tax on gross, not net.
total = apply_tax(subtotal)
total = apply_discount(total)

# Koenig lookup requires the argument type to be in scope.
# See https://en.cppreference.com/w/cpp/language/adl
```
