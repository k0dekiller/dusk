  # Database

## Assumptions

### Idempotency
Any query method that returns `None` that doesn't affect any rows (e.g. deleting a nonexistent resource, archiving an already archived resource) will raise the `NoRowsAffectedError` or one of its subclasses.

## Functions

### `.get()`

Returns the entire `Row` object or `None` if no match.

### `.exists()`

Returns `True` if a `Row` object is present.

### `.valid()`

Returns `True` if a `Row` object is not archived.

> [!NOTE]
> This function, despite its name, doesn't include any table-specific logic to determine if a `Row`'s resource is actually valid. Any server-side logic is still in `server/app.py` or in other table-specific database functions.

### `.archived()`

Returns `True` if a `Row` object is archived.

## Structure

- [x] `invites`
    - [x] `id`
    - [x] `code`
    - [x] `owner` **→** `users.id`
    - [x] `max_uses`
    - [x] `created_at`
    - [x] `use_count`
    - [x] `archived_at?`
    - [ ] `expires_at?`
- [x] `users`
    - [x] `id`
    - [x] `username`
    - [x] `password_hash`
    - [x] `archived_at?`
    - [x] `created_at`
- [x] `tokens`
    - [x] `id`
    - [x] `user_id` **→** `users.id`
    - [x] `archived_at?`
    - [x] `token_hash`
    - [x] `created_at`
    - [x] `last_used_at?`