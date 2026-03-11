# Version Resolution

The `rpm` CLI resolves PEP 440 version specifiers against git tags using `git ls-remote`.

## How It Works

1. If `rev_spec` contains no PEP 440 operators (`~=`, `>=`, `<`, `*`, etc.), it is returned as-is (branch/tag passthrough)
2. If `rev_spec` contains operators:
   - Runs `git ls-remote --tags <url>` to list all tags
   - Parses version suffixes with `packaging.version.Version`
   - Filters with `packaging.specifiers.SpecifierSet(rev_spec)`
   - Returns the highest matching tag
3. Fails fast if no match found

## Supported Specifiers

| Specifier | Meaning | Example Match |
|---|---|---|
| `~=1.0.0` | `>=1.0.0, <1.1.0` | `1.0.3` |
| `>=1.0.0,<2.0.0` | Range | `1.5.2` |
| `==1.2.3` | Exact | `1.2.3` |
| `>=1.0.0` | Minimum | `3.0.0` |
| `!=1.0.1` | Exclusion | `1.0.0`, `1.0.2` |
| `*` | Latest | highest available |

## Branch/Tag Passthrough

Plain strings without operators are returned unchanged:

- `main` -> `main`
- `caylent-2.0.0` -> `caylent-2.0.0`
- `v1.0.0` -> `v1.0.0`

## Error Cases

- No tags found for the URL -> fail with error
- No parseable version tags -> fail with error
- No tags matching the specifier -> fail with available versions listed
- `git ls-remote` failure -> fail with stderr
