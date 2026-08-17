# Database structure

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

# Assumptions

## Idempotency
Any query method that returns `None` that doesn't affect any rows (e.g. deleting a nonexistent resource, archiving an already archived resource) will raise the `NoRowsAffectedError` or one of its subclasses.