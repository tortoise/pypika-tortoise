# ChangeLog

## 0.6

### 0.6.0 (Unreleased)

- Drop support for Python3.8 (#25)
- fix: failed to run poetry add pypika-tortoise with 'poetry>=2.0' (#26)

## 0.5

### 0.5.0

- Replace `get_sql` kwargs with `SqlContext` to improve performance

## 0.4

### 0.4.0
- Rename package name from `pypika` to `pypika_tortoise`

## 0.3

### 0.3.2
- Added `QueryBuilder.get_parameterized_sql`

### 0.3.1
- `Array` can be parametrized

### 0.3.0
- Add `Parameterizer`
- Uppdate `Parameter` to be dialect-aware
- Remove `ListParameter`, `DictParameter`, `QmarkParameter`, etc.
- Wrap query's offset and limit with ValueWrapper so they can be parametrized
- Fix a missing whitespace for MSSQL when pagination without ordering is used

## 0.2

### 0.2.2
- Fix enums not quoted. (#7)
- Drop python3.7 support
- Move all custom Exception class to `pypika.exceptions`
- Apply bandit check in ci
- Pass mypy check and add it to ci

### 0.2.1
- Fix stringification of datetime objects

### 0.2.0
- Improved parameterized queries support

## 0.1

### 0.1.6

- Fix `UPDATE JOIN` statement. (#3)

### 0.1.5

- Add `MSSQL` dialect.
- Add `Oracle` dialect.
- Fix `WITH RECURSIVE` support.

### 0.1.4

- Add postgres `timetz` support.

### 0.1.3

- Change `postgres` and `sqlite` in `Dialects` enum.
- Refactor `on conflict` statement.
- Support `upsert` statement.

### 0.1.2

- Add support for `with recursive`.
- Add `insert` ignore support.

### 0.1.1

- Add support for `sqlite` and `MySQL` with `limit` and `order by` in `delete` and `update`.

### 0.1.0

- First release version.
