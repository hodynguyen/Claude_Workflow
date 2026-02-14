---
description: Generate a CI-compatible test report from test results. Supports GitHub Actions annotations, JUnit XML, and Markdown summary formats.
---

# /hody-workflow:ci-report

Generate a CI-compatible test report for the current project.

## Steps

1. **Check initialization**: Verify `.hody/profile.yaml` exists. If not, tell the user to run `/hody-workflow:init` first.

2. **Read profile**: Read `.hody/profile.yaml` to determine:
   - Testing framework (jest, vitest, pytest, go-test, cargo-test, junit, rspec, phpunit, etc.)
   - CI system (github-actions, gitlab-ci, jenkins, or none)

3. **Detect test results**: Look for existing test results or offer to run tests:
   - If test result files exist (e.g., `test-results/`, `coverage/`, `junit.xml`), parse them
   - If no results exist, ask the user whether to run the test suite now

4. **Choose output format** based on CI system:

| CI System | Primary Format | Secondary Format |
|-----------|---------------|-----------------|
| GitHub Actions | GitHub annotations (stdout) | Markdown summary (`test-results/summary.md`) |
| GitLab CI | JUnit XML (`test-results/junit.xml`) | Markdown summary |
| Jenkins | JUnit XML (`test-results/junit.xml`) | — |
| None / Unknown | Markdown summary (`test-results/summary.md`) | — |

5. **Generate the report** using the `ci-report` output style template from `output-styles/ci-report.md`:
   - Parse test output (pass/fail/skip counts, failed test details, timing)
   - Format according to the chosen template
   - Include coverage data if available

6. **Write report files**:
   - Create `test-results/` directory if needed
   - Write the report file(s) in the appropriate format
   - Display a summary to the user

## Output

Display a summary after generating:

```
CI Report Generated
━━━━━━━━━━━━━━━━━━

CI System: GitHub Actions
Format: GitHub Annotations + Markdown Summary

Results:
  Passed:  42
  Failed:  2
  Skipped: 3
  Total:   47

Report files:
  → test-results/summary.md (Markdown)
  → stdout annotations (copy to CI workflow)

Failed tests:
  ✗ test_login_invalid_token (tests/auth.test.ts:42)
  ✗ test_rate_limit_exceeded (tests/api.test.ts:88)
```

## Notes

- This command reads `.hody/profile.yaml` for CI and testing config
- Report files are written to `test-results/` directory
- Add `test-results/` to `.gitignore` if you don't want to commit reports
- For GitHub Actions, copy the annotation output to your workflow's step output
- Supports all testing frameworks detected by `detect_stack.py`
