# Source Patterns

Use this reference when the source URL is not immediately fetchable.

## GitHub Tree URL

Pattern:

```text
https://github.com/<owner>/<repo>/tree/<ref>/<path-inside-repo>
```

Workflow:

```bash
git clone --filter=blob:none --no-checkout https://github.com/<owner>/<repo>.git <tmp>
cd <tmp>
git checkout <ref>
git sparse-checkout init --cone
git sparse-checkout set <path-inside-repo>
```

If `<ref>` may contain slashes, inspect `git ls-remote --heads --tags origin` and choose the longest matching branch or tag prefix from the URL.

## GitHub Blob URL

Pattern:

```text
https://github.com/<owner>/<repo>/blob/<ref>/<file>
```

Fetch the repository at `<ref>` and compare the containing skill directory when possible. Use a raw file download only for one-file sources.

## Local Or Archive Source

If the source is a local path, zip, tarball, or copied folder, copy or extract it into a temporary directory first. Do not compare directly against a mutable source directory unless the user says it is safe.

## Missing Source

Do not infer a source from a similar skill name alone. Search README, frontmatter, comments, and adjacent metadata. If no reliable source remains, skip that skill and ask for the original location.
