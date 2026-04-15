# Integration Test Plan -- rpm-git-repo

Manual and agent-executable integration tests for the
[rpm-git-repo](https://github.com/caylent-solutions/rpm-git-repo) tool.
These tests exercise PEP 440 version constraint resolution in manifest
XML `<project revision>` attributes using local `file://` Git repos.

---

## Prerequisites

### 1. Install rpm-git-repo

```bash
pip install rpm-git-repo
```

Verify:

```bash
repo --help
```

### 2. Python 3.11+

```bash
python3 --version
```

### 3. Git

```bash
git --version
```

### 4. Clean Test Directory

```bash
rm -rf /tmp/repo-tool-tests
mkdir -p /tmp/repo-tool-tests
```

---

## Setup: Create Local Test Fixture Repos

All tests use local `file://` Git repos. Run this setup once before
executing any test categories.

### Package Repo with Tagged Versions

Create a Git repo with multiple semver tags under a `my-pkg/` namespace:

```bash
cd /tmp/repo-tool-tests
mkdir pkg-repo && cd pkg-repo
git init -b main
git config user.email "test@test.com"
git config user.name "test"

echo "v1" > README.md
git add -A && git commit -m "initial"

for tag in my-pkg/0.1.0 my-pkg/0.2.0 my-pkg/0.2.1 my-pkg/0.3.0 \
           my-pkg/1.0.0 my-pkg/1.1.0 my-pkg/2.0.0; do
  echo "$tag" >> versions.txt
  git add -A && git commit -m "tag $tag"
  git tag "$tag"
done
```

**Expected tags:**

```bash
git tag -l "my-pkg/*"
# my-pkg/0.1.0
# my-pkg/0.2.0
# my-pkg/0.2.1
# my-pkg/0.3.0
# my-pkg/1.0.0
# my-pkg/1.1.0
# my-pkg/2.0.0
```

### Manifest Repo with Test Manifests

Create a manifest repo with a shared `remote.xml` and one manifest per
test case:

```bash
cd /tmp/repo-tool-tests
mkdir -p manifest-repo/repo-specs/git-connection
cd manifest-repo
git init -b main
git config user.email "test@test.com"
git config user.name "test"
```

#### remote.xml

```bash
cat > repo-specs/git-connection/remote.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="local" fetch="file:///tmp/repo-tool-tests/" />
  <default revision="main" remote="local" sync-j="4" />
</manifest>
EOF
```

#### Test Manifests

Create one manifest per constraint type. Each references the package
repo with a different `revision` attribute:

```bash
# M1: Compatible release (~=0.2.0 means >=0.2.0, <0.3.0)
cat > repo-specs/test-m1.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <include name="repo-specs/git-connection/remote.xml" />
  <project name="pkg-repo" path=".packages/test-m1" remote="local"
           revision="refs/tags/my-pkg/~=0.2.0" />
</manifest>
EOF

# M2: Compatible release (exact match)
cat > repo-specs/test-m2.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <include name="repo-specs/git-connection/remote.xml" />
  <project name="pkg-repo" path=".packages/test-m2" remote="local"
           revision="refs/tags/my-pkg/~=0.2.1" />
</manifest>
EOF

# M3: Range constraint (>=0.2.0, <1.0.0)
# Note: < must be XML-escaped as &lt; in attributes
cat > repo-specs/test-m3.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <include name="repo-specs/git-connection/remote.xml" />
  <project name="pkg-repo" path=".packages/test-m3" remote="local"
           revision="refs/tags/my-pkg/>=0.2.0,&lt;1.0.0" />
</manifest>
EOF

# M4: Range in major 1 (>=1.0.0, <2.0.0)
cat > repo-specs/test-m4.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <include name="repo-specs/git-connection/remote.xml" />
  <project name="pkg-repo" path=".packages/test-m4" remote="local"
           revision="refs/tags/my-pkg/>=1.0.0,&lt;2.0.0" />
</manifest>
EOF

# M5: Minimum only (>=1.0.0)
cat > repo-specs/test-m5.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <include name="repo-specs/git-connection/remote.xml" />
  <project name="pkg-repo" path=".packages/test-m5" remote="local"
           revision="refs/tags/my-pkg/>=1.0.0" />
</manifest>
EOF

# M6: Wildcard (latest)
cat > repo-specs/test-m6.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <include name="repo-specs/git-connection/remote.xml" />
  <project name="pkg-repo" path=".packages/test-m6" remote="local"
           revision="refs/tags/my-pkg/*" />
</manifest>
EOF

# M7: Exact match (==1.0.0)
cat > repo-specs/test-m7.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <include name="repo-specs/git-connection/remote.xml" />
  <project name="pkg-repo" path=".packages/test-m7" remote="local"
           revision="refs/tags/my-pkg/==1.0.0" />
</manifest>
EOF

# M8: Exclusion (!=1.0.0)
cat > repo-specs/test-m8.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <include name="repo-specs/git-connection/remote.xml" />
  <project name="pkg-repo" path=".packages/test-m8" remote="local"
           revision="refs/tags/my-pkg/!=1.0.0" />
</manifest>
EOF

# M9: No matching tags (should fail)
cat > repo-specs/test-m9.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <include name="repo-specs/git-connection/remote.xml" />
  <project name="pkg-repo" path=".packages/test-m9" remote="local"
           revision="refs/tags/my-pkg/~=9.0.0" />
</manifest>
EOF

# M10: Exact tag (passthrough, no constraint)
cat > repo-specs/test-m10.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <include name="repo-specs/git-connection/remote.xml" />
  <project name="pkg-repo" path=".packages/test-m10" remote="local"
           revision="refs/tags/my-pkg/0.2.0" />
</manifest>
EOF

# M11: Branch (passthrough)
cat > repo-specs/test-m11.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <include name="repo-specs/git-connection/remote.xml" />
  <project name="pkg-repo" path=".packages/test-m11" remote="local"
           revision="main" />
</manifest>
EOF
```

Commit all manifests:

```bash
git add -A && git commit -m "all test manifests"
```

---

## Category 1: PEP 440 Constraint Resolution (M1-M11)

For each test, create a project directory, run `repo init` + `repo sync`,
and verify the expected tag was checked out.

### Expected Results

| Test | Revision | Expected Tag | Description |
|------|----------|-------------|-------------|
| M1 | `refs/tags/my-pkg/~=0.2.0` | `my-pkg/0.2.1` | Compatible release (highest 0.2.x) |
| M2 | `refs/tags/my-pkg/~=0.2.1` | `my-pkg/0.2.1` | Exact compatible |
| M3 | `refs/tags/my-pkg/>=0.2.0,<1.0.0` | `my-pkg/0.3.0` | Range (highest <1.0.0) |
| M4 | `refs/tags/my-pkg/>=1.0.0,<2.0.0` | `my-pkg/1.1.0` | Range in major 1 |
| M5 | `refs/tags/my-pkg/>=1.0.0` | `my-pkg/2.0.0` | Minimum only (highest overall) |
| M6 | `refs/tags/my-pkg/*` | `my-pkg/2.0.0` | Wildcard (latest) |
| M7 | `refs/tags/my-pkg/==1.0.0` | `my-pkg/1.0.0` | Exact match |
| M8 | `refs/tags/my-pkg/!=1.0.0` | `my-pkg/2.0.0` | Exclusion (highest except 1.0.0) |
| M9 | `refs/tags/my-pkg/~=9.0.0` | ERROR | No matching tags |
| M10 | `refs/tags/my-pkg/0.2.0` | `my-pkg/0.2.0` | Exact tag passthrough |
| M11 | `main` | `main` | Branch passthrough |

### Running Tests

For each test M1-M11:

```bash
TEST_NUM=1  # Change for each test

rm -rf /tmp/repo-tool-tests/project-m${TEST_NUM}
mkdir /tmp/repo-tool-tests/project-m${TEST_NUM}
cd /tmp/repo-tool-tests/project-m${TEST_NUM}

repo init \
  -u file:///tmp/repo-tool-tests/manifest-repo \
  -b main \
  -m repo-specs/test-m${TEST_NUM}.xml \
  --no-clone-bundle

repo sync

# Verify which tag was checked out (M1-M8, M10)
cd .packages/test-m${TEST_NUM}
git describe --tags --exact-match HEAD 2>&1
```

### Pass Criteria

- **M1-M8, M10-M11:** `repo sync` exits 0 and the correct tag is checked out
- **M9:** `repo sync` exits non-zero with a clear error about no matching tags

---

## Category 2: Constraint Detection (Unit-Level Verification)

Verify that `version_constraints.is_version_constraint()` correctly
identifies all supported constraint patterns.

```bash
cd /path/to/rpm-git-repo
python3 -c "
import version_constraints as vc
tests = [
    ('refs/tags/my-pkg/~=0.2.0', True),
    ('refs/tags/my-pkg/>=1.0.0', True),
    ('refs/tags/my-pkg/>=1.0.0,<2.0.0', True),
    ('refs/tags/my-pkg/*', True),
    ('refs/tags/my-pkg/==1.0.0', True),
    ('refs/tags/my-pkg/!=1.0.0', True),
    ('refs/tags/my-pkg/<2.0.0', True),
    ('refs/tags/my-pkg/<=2.0.0', True),
    ('refs/tags/my-pkg/0.2.0', False),  # exact tag, not a constraint
    ('main', False),                     # branch, not a constraint
    ('abc123def', False),                # SHA, not a constraint
]
for rev, expected in tests:
    result = vc.is_version_constraint(rev)
    status = 'PASS' if result == expected else 'FAIL'
    print(f'{status}: is_version_constraint({rev!r}) = {result} (expected {expected})')
"
```

**Pass criteria:** All lines show PASS.

---

## Category 3: Constraint Resolution (Unit-Level Verification)

Verify that `version_constraints.resolve_version_constraint()` selects
the correct tag from a list.

```bash
cd /path/to/rpm-git-repo
python3 -c "
import version_constraints as vc
tags = [
    'refs/tags/my-pkg/0.1.0',
    'refs/tags/my-pkg/0.2.0',
    'refs/tags/my-pkg/0.2.1',
    'refs/tags/my-pkg/0.3.0',
    'refs/tags/my-pkg/1.0.0',
    'refs/tags/my-pkg/1.1.0',
    'refs/tags/my-pkg/2.0.0',
]
tests = [
    ('refs/tags/my-pkg/~=0.2.0', 'refs/tags/my-pkg/0.2.1'),
    ('refs/tags/my-pkg/>=0.2.0,<1.0.0', 'refs/tags/my-pkg/0.3.0'),
    ('refs/tags/my-pkg/>=1.0.0,<2.0.0', 'refs/tags/my-pkg/1.1.0'),
    ('refs/tags/my-pkg/>=1.0.0', 'refs/tags/my-pkg/2.0.0'),
    ('refs/tags/my-pkg/*', 'refs/tags/my-pkg/2.0.0'),
    ('refs/tags/my-pkg/==1.0.0', 'refs/tags/my-pkg/1.0.0'),
]
for constraint, expected in tests:
    result = vc.resolve_version_constraint(constraint, tags)
    status = 'PASS' if result == expected else 'FAIL'
    print(f'{status}: resolve({constraint!r}) = {result!r} (expected {expected!r})')
"
```

**Pass criteria:** All lines show PASS.

---

## Category 4: Error Cases

### EC-1: No matching tags

```bash
cd /tmp/repo-tool-tests
rm -rf project-ec1 && mkdir project-ec1 && cd project-ec1
repo init \
  -u file:///tmp/repo-tool-tests/manifest-repo \
  -b main \
  -m repo-specs/test-m9.xml \
  --no-clone-bundle
repo sync 2>&1; echo "EXIT: $?"
```

**Pass criteria:** Exit non-zero. Error message mentions the constraint
and indicates no matching tags.

### EC-2: Invalid remote URL

Create a manifest pointing to a non-existent repo:

```bash
cd /tmp/repo-tool-tests/manifest-repo
cat > repo-specs/test-ec2.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="bad" fetch="file:///tmp/nonexistent/" />
  <project name="nonexistent" path=".packages/test-ec2" remote="bad"
           revision="refs/tags/my-pkg/~=1.0.0" />
</manifest>
EOF
git add -A && git commit -m "ec2"
```

```bash
rm -rf /tmp/repo-tool-tests/project-ec2
mkdir /tmp/repo-tool-tests/project-ec2 && cd /tmp/repo-tool-tests/project-ec2
repo init \
  -u file:///tmp/repo-tool-tests/manifest-repo \
  -b main \
  -m repo-specs/test-ec2.xml \
  --no-clone-bundle
repo sync 2>&1; echo "EXIT: $?"
```

**Pass criteria:** Exit non-zero. Error message mentions failed to list
remote tags or failed to fetch.

---

## Category 5: Passthrough Behavior

Verify that non-constraint revisions are unaffected by the constraint
resolution code path.

### PT-1: Exact tag passthrough

Use M10 (`refs/tags/my-pkg/0.2.0`). Verify `repo sync` checks out
exactly `my-pkg/0.2.0`.

### PT-2: Branch passthrough

Use M11 (`main`). Verify `repo sync` checks out the `main` branch.

### PT-3: SHA passthrough

Create a manifest with a full commit SHA as the revision:

```bash
cd /tmp/repo-tool-tests/pkg-repo
SHA=$(git rev-parse my-pkg/1.0.0)
echo "SHA for 1.0.0: $SHA"
```

Create a manifest using this SHA, run `repo sync`, and verify the
correct commit is checked out.

**Pass criteria:** All passthroughs work identically to before the
constraint resolution feature was added.

---

## Category 6: Idempotency

### ID-1: Double sync with constraint

Run `repo sync` twice with a constraint revision. The second run should
succeed without re-resolving (the tag is already checked out locally).

```bash
rm -rf /tmp/repo-tool-tests/project-id1
mkdir /tmp/repo-tool-tests/project-id1 && cd /tmp/repo-tool-tests/project-id1
repo init \
  -u file:///tmp/repo-tool-tests/manifest-repo \
  -b main \
  -m repo-specs/test-m1.xml \
  --no-clone-bundle

repo sync; echo "FIRST: $?"
repo sync; echo "SECOND: $?"
```

**Pass criteria:** Both syncs exit 0.

---

## Category 7: Multi-Project Manifests

### MP-1: Two projects with different constraints

Create a manifest with two projects using different constraint types:

```bash
cd /tmp/repo-tool-tests/manifest-repo
cat > repo-specs/test-mp1.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <include name="repo-specs/git-connection/remote.xml" />
  <project name="pkg-repo" path=".packages/pkg-compat" remote="local"
           revision="refs/tags/my-pkg/~=0.2.0" />
  <project name="pkg-repo" path=".packages/pkg-range" remote="local"
           revision="refs/tags/my-pkg/>=1.0.0,&lt;2.0.0" />
</manifest>
EOF
git add -A && git commit -m "multi-project"
```

```bash
rm -rf /tmp/repo-tool-tests/project-mp1
mkdir /tmp/repo-tool-tests/project-mp1 && cd /tmp/repo-tool-tests/project-mp1
repo init \
  -u file:///tmp/repo-tool-tests/manifest-repo \
  -b main \
  -m repo-specs/test-mp1.xml \
  --no-clone-bundle
repo sync 2>&1; echo "EXIT: $?"

# Verify each project resolved correctly
cd .packages/pkg-compat && git describe --tags --exact-match HEAD 2>&1
cd ../../.packages/pkg-range && git describe --tags --exact-match HEAD 2>&1
```

**Pass criteria:** Exit 0. `pkg-compat` at `my-pkg/0.2.1`,
`pkg-range` at `my-pkg/1.1.0`.

---

## How to Run

### Full Test Suite (All Categories)

```bash
# 1. Setup fixtures
# (Run the setup commands from the "Setup" section above)

# 2. Run Categories 1-7 sequentially
# Each category documents its own commands and pass criteria

# 3. Cleanup
rm -rf /tmp/repo-tool-tests
```

### Running Individual Categories

Each category is independent. Run the setup once, then execute any
category in any order.

### Cleanup

```bash
rm -rf /tmp/repo-tool-tests
```

Remove any `repo init` state from test directories if re-running:

```bash
rm -rf /tmp/repo-tool-tests/project-*
```
