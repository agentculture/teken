# afi-cli — deprecated alias for `teken`

`afi-cli` was renamed to **[`teken`](https://pypi.org/project/teken/)** (Hebrew
תֶּקֶן, "standard"). This package is a thin compatibility wrapper: installing it
pulls in `teken`, which provides the canonical `teken` command and a deprecated
`afi` alias.

```bash
uv tool install afi-cli   # still works — installs teken under the hood
uv tool install teken     # preferred going forward
```

New code should depend on `teken` directly. This wrapper is published in
lockstep with `teken` and will be retired once the migration window closes.
