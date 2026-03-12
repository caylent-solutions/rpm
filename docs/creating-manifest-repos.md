# Creating a Manifest Repository

How to create a top-level manifest repository that orchestrates RPM packages.

## What is a Manifest Repository?

A manifest repository is a Git repository that contains XML manifest files defining which packages to sync, from which repositories, at which versions. It acts as the central registry for an organization's automation packages.

The RPM CLI reads `.rpmenv` configurations that point to manifest files in these repositories. When `rpm configure` runs, it uses the [repo tool](https://gerrit.googlesource.com/git-repo/) to clone and sync packages according to the manifest definitions.

## Repository Structure

```text
my-manifest-repo/
├── repo-specs/
│   ├── git-connection/
│   │   └── remote.xml              # Shared remote definitions
│   └── common/
│       └── <archetype>/
│           └── development/
│               └── <language>/
│                   └── <toolchain>/
│                       ├── build-meta.xml          # Entry-point manifest
│                       ├── packages.xml            # Package declarations
│                       └── claude-marketplaces.xml  # Optional: marketplace packages
├── catalog/                         # Optional: task runner templates for rpm bootstrap
│   ├── make/
│   │   └── Makefile
│   ├── gradle/
│   │   ├── build.gradle
│   │   └── rpm-bootstrap.gradle
│   └── rpm/
│       └── rpm-readme.md            # Getting-started guide (.rpmenv + readme only)
├── examples/                        # Optional: example bootstrapped projects
└── README.md
```

## Remote Definitions (remote.xml)

The `remote.xml` file defines Git remotes that manifests reference. It uses `${VARIABLE}` placeholders resolved by `repo envsubst` at sync time:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin"
          fetch="${GITBASE}" />

  <default revision="main"
           remote="origin"
           sync-j="4" />
</manifest>
```

The `GITBASE` variable comes from `.rpmenv` and defines the base URL for all package repositories.

## Package Manifests (packages.xml)

Package manifests declare which repositories to clone and where to place them:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <include name="repo-specs/git-connection/remote.xml" />

  <project name="my-build-conventions"
           path=".packages/my-build-conventions"
           remote="origin"
           revision="refs/tags/1.0.0">
  </project>

  <project name="my-linting-rules"
           path=".packages/my-linting-rules"
           remote="origin"
           revision="refs/tags/2.1.0">
  </project>
</manifest>
```

Key attributes:

- `name` — repository name (appended to the remote's `fetch` URL)
- `path` — local directory where the repo is cloned (always under `.packages/`)
- `remote` — name of the remote defined in `remote.xml`
- `revision` — Git ref to checkout (tag, branch, or PEP 440 constraint)

## Entry-Point Manifests (meta.xml / build-meta.xml)

An entry-point manifest ties everything together with `<include>` tags:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <include name="repo-specs/common/my-archetype/packages.xml" />
  <include name="repo-specs/common/my-archetype/claude-marketplaces.xml" />
</manifest>
```

This is the file referenced by `RPM_SOURCE_<name>_PATH` in `.rpmenv`.

## Cascading Manifest Hierarchy (Optional)

Manifests support cascading inheritance through `<include>` chains. This is optional but useful for organizations with many project archetypes that share common packages.

Each level in the hierarchy includes its parent:

```text
meta.xml (entry point)
  └── packages.xml (leaf — e.g., microservice)
        └── packages.xml (framework — e.g., spring-boot)
              └── packages.xml (language — e.g., java)
                    └── packages.xml (common — shared across all)
```

A leaf manifest includes its parent, which includes its parent, forming a chain. Packages defined at any level are available to all descendants.

This hierarchy is not required — a flat structure with a single `packages.xml` works for simple setups.

## Providing a Remote Catalog

A manifest repository can also serve as a remote catalog for `rpm bootstrap`. Place task runner templates in a `catalog/` directory at the repository root:

```text
catalog/
├── make/
│   ├── Makefile
│   └── rpm-readme.md
├── gradle/
│   ├── build.gradle
│   ├── rpm-bootstrap.gradle
│   └── rpm-readme.md
└── rpm/
    └── rpm-readme.md
```

Each runner directory includes an `rpm-readme.md` with prerequisites, setup instructions, and a `.rpmenv` variable reference. The `rpm/` runner produces only `.rpmenv` and the readme -- no task runner wrapper files -- for users who invoke the RPM CLI directly.

Users can then bootstrap projects using your catalog:

```bash
rpm bootstrap make --catalog-source 'https://github.com/org/my-manifest-repo.git@main'
```

Or via environment variable:

```bash
export RPM_CATALOG_SOURCE='https://github.com/org/my-manifest-repo.git@v1.0.0'
rpm bootstrap gradle
```

## Connecting to .rpmenv

The `.rpmenv` file in a consumer project points to your manifest repository:

```properties
RPM_SOURCE_build_URL=https://github.com/org/my-manifest-repo.git
RPM_SOURCE_build_REVISION=v1.0.0
RPM_SOURCE_build_PATH=repo-specs/common/my-archetype/build-meta.xml
```

Multiple sources can reference different manifest repositories, enabling teams to compose packages from multiple organizations.

See the [multi-source guide](multi-source-guide.md) for details on multi-source configurations.
