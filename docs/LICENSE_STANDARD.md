# License Standard: GNU GPL v3.0

> **Standard Adopted**: 2025-12-09
> **Applies To**: All dev-nexus projects and monitored repositories

---

## Overview

All projects monitored by dev-nexus must use the **GNU General Public License v3.0 (GPL-3.0)** as their licensing standard. This ensures software freedom, copyleft protection, and consistency across the ecosystem.

---

## Why GPL v3.0?

### Core Principles

1. **Software Freedom**
   - Users have the freedom to run, study, modify, and distribute the software
   - "Free" as in "freedom", not just price

2. **Copyleft Protection**
   - Derivative works must also be GPL-3.0
   - Prevents proprietary forks that restrict user freedoms
   - Ensures improvements benefit the entire community

3. **Patent Protection**
   - Contributors grant patent licenses to users
   - Protection against patent litigation
   - Safe for users and contributors

4. **Community Alignment**
   - Compatible with other GPL projects
   - Encourages open collaboration
   - Builds trust with open-source community

5. **Long-term Sustainability**
   - Code remains free forever
   - Cannot be relicensed to proprietary
   - Protects against commercialization that restricts access

---

## Requirements

### 1. LICENSE File

**Mandatory:** Every repository must include a `LICENSE` file in the root directory.

**Requirements:**
- ✅ Must contain the complete, unmodified GNU GPL v3.0 text
- ✅ Minimum 30KB file size (full text)
- ✅ Must include "GNU GENERAL PUBLIC LICENSE" header
- ✅ Must specify "Version 3, 29 June 2007"

**Where to get it:**
- Download from: https://www.gnu.org/licenses/gpl-3.0.txt
- Copy from dev-nexus: [LICENSE](../LICENSE)

### 2. README.md Badge

**Mandatory:** Include GPL v3 badge in README.md

**Badge code:**
```markdown
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
```

**Rendered badge:**
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

**Placement:** Near the top of README.md, typically after the title

### 3. README.md License Section

**Mandatory:** Include a License section explaining GPL v3

**Minimum content:**
```markdown
## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).

See the [LICENSE](LICENSE) file for details.
```

**Recommended (more detailed):**
```markdown
## License

This project is licensed under the **GNU General Public License v3.0** (GPL-3.0).

**What this means:**
- ✅ **Free to use** for any purpose
- ✅ **Free to modify** and create derivative works
- ✅ **Free to distribute** copies
- ⚠️ **Copyleft**: Derivative works must also be GPL-3.0
- ✅ **Patent protection** for users
- ✅ **Source code** must remain available

See the [LICENSE](LICENSE) file for full details or visit [https://www.gnu.org/licenses/gpl-3.0](https://www.gnu.org/licenses/gpl-3.0).

**Why GPL v3?** This ensures that all improvements and derivative works benefit the entire community and remain free software.
```

### 4. Source File Headers (Recommended)

**Optional but recommended:** Add GPL headers to source files

**Python example:**
```python
# Copyright (C) 2025  Your Name <email@example.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
```

**JavaScript example:**
```javascript
/*
 * Copyright (C) 2025  Your Name <email@example.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */
```

---

## Automated Checking

The **Documentation Standards Checker** automatically verifies license compliance:

### Checks Performed

1. **LICENSE File Existence**
   - Checks if `LICENSE` file exists in repository root
   - **Severity if missing:** CRITICAL

2. **GPL v3 Verification**
   - Verifies LICENSE contains "GNU GENERAL PUBLIC LICENSE"
   - Verifies LICENSE specifies "Version 3"
   - **Severity if wrong:** CRITICAL

3. **Complete License Text**
   - Checks file size is at least 30KB (full GPL text)
   - **Severity if incomplete:** HIGH

4. **README Badge**
   - Checks if README.md includes GPL v3 badge or reference
   - **Severity if missing:** HIGH

5. **README License Section**
   - Checks if README.md has a License section
   - **Severity if missing:** MEDIUM

### Using the Checker

**Via A2A API:**
```bash
curl -X POST https://your-dev-nexus.run.app/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "check_documentation_standards",
    "input": {
      "repository": "username/repository",
      "check_all_docs": false
    }
  }'
```

**Programmatically:**
```python
from github import Github
from core.documentation_standards_checker import DocumentationStandardsChecker

github_client = Github("your_token")
checker = DocumentationStandardsChecker(github_client)

result = checker.check_repository("username/repository")

# Check for license violations
for file_result in result['file_results']:
    if file_result['file'] == 'LICENSE':
        for violation in file_result['violations']:
            print(f"License violation: {violation['message']}")
```

---

## Non-Compliance

### What Happens

If a repository does not comply with GPL v3 requirements:

1. **Documentation Checker Reports:**
   - Status: ❌ Non-Compliant
   - CRITICAL violations logged
   - Compliance score significantly reduced

2. **Recommendations Generated:**
   - "⚠️ CRITICAL: Replace LICENSE file with complete GNU GPL v3.0 text"
   - "Add GPL v3 badge to README.md"
   - "Add License section to README.md"

3. **Pattern Discovery:**
   - Non-compliance patterns detected
   - Similar issues flagged across repositories
   - Notifications sent to maintainers

### Remediation

**Quick fix checklist:**
- [ ] Download GPL v3 text from https://www.gnu.org/licenses/gpl-3.0.txt
- [ ] Save as `LICENSE` in repository root
- [ ] Add GPL v3 badge to README.md (near title)
- [ ] Add License section to README.md (near end)
- [ ] Commit changes: `git add LICENSE README.md && git commit -m "Add GPL v3 license"`
- [ ] Push: `git push`
- [ ] Re-run documentation checker to verify

---

## FAQ

### Why must we use GPL v3 specifically?

**Consistency:** Using a single license across all projects simplifies collaboration, reduces legal complexity, and builds trust with the community.

**Freedom:** GPL v3 is the strongest copyleft license, ensuring all derivative works remain free software.

**Protection:** Includes patent protection clauses and protects against tivoization (hardware restrictions).

### Can I use MIT, Apache, or other licenses?

**No.** To maintain consistency across the dev-nexus ecosystem, all projects must use GPL v3. If you need different licensing for specific use cases, discuss with the project maintainers.

### What if my project was already using a different license?

**Migration required.** If you control all copyright (or can get permission from all contributors), you can relicense to GPL v3. See the remediation checklist above.

### Can I add additional terms to GPL v3?

**Limited.** GPL v3 allows some additional permissions (Section 7), but not additional restrictions. Any modifications must be compatible with GPL v3 terms. Consult legal advice before modifying.

### What about libraries and dependencies?

**GPL-compatible licenses OK:** Your project can depend on libraries with GPL-compatible licenses:
- GPL v2 (can be upgraded to v3)
- LGPL (Lesser GPL)
- BSD licenses (2-clause, 3-clause)
- MIT license
- Apache License 2.0

**Incompatible licenses forbidden:** Cannot depend on:
- Proprietary/closed-source libraries (for distribution)
- Licenses with additional restrictions incompatible with GPL

### Does GPL v3 prevent commercial use?

**No!** GPL v3 is fully compatible with commercial use. You can:
- ✅ Sell GPL-licensed software
- ✅ Provide commercial support/services
- ✅ Use in commercial products

**Requirement:** You must provide source code to users and allow them the same freedoms (modify, redistribute, etc.).

### What about SaaS / Cloud services?

**GPL v3 does not require source disclosure for SaaS.** If you run the software as a service without distributing it, you don't need to provide source to users.

**Note:** If distribution/licensing obligations are a concern, consult the GNU Affero GPL (AGPL v3), which has network provisions.

---

## Resources

### Official GPL v3 Documentation

- **Full License Text:** https://www.gnu.org/licenses/gpl-3.0.txt
- **GPL v3 Quick Guide:** https://www.gnu.org/licenses/quick-guide-gplv3.html
- **GPL FAQ:** https://www.gnu.org/licenses/gpl-faq.html
- **Why GPL?** https://www.gnu.org/licenses/why-not-lgpl.html

### Understanding GPL v3

- **GPL v3 Explained:** https://copyleft.org/guide/comprehensive-gpl-guidepa1.html
- **GPL Compatibility:** https://www.gnu.org/licenses/license-compatibility.html
- **Using GPL v3:** https://www.fsf.org/licensing/

### License Checker Tools

- **GitHub License Detector:** Built into GitHub
- **SPDX License List:** https://spdx.org/licenses/
- **Choose a License:** https://choosealicense.com/licenses/gpl-3.0/

### Dev-Nexus Tools

- **Documentation Standards:** [DOCUMENTATION_STANDARDS.md](./DOCUMENTATION_STANDARDS.md)
- **Standards Checker:** `core/documentation_standards_checker.py`
- **Example LICENSE:** [LICENSE](../LICENSE)
- **A2A Skill:** `check_documentation_standards`

---

## Enforcement

### Automatic Enforcement

- ✅ Documentation standards checker verifies GPL v3 on every run
- ✅ Pattern discovery agent flags license inconsistencies
- ✅ GitHub Actions can block PRs with non-compliant licenses (optional)

### Manual Review

- Project maintainers should verify license compliance during code review
- New projects should be checked before adding to dev-nexus monitoring
- Existing projects should be audited and migrated if necessary

### Exceptions

**None.** All projects must use GPL v3. If exceptions are needed, discuss with project leadership.

---

## Summary

**GPL v3 Standard Checklist:**

- [x] LICENSE file with complete GPL v3 text in repository root
- [x] README.md includes GPL v3 badge
- [x] README.md includes License section
- [ ] Source files include license headers (optional but recommended)
- [x] Documentation standards checker configured
- [x] All contributors understand GPL v3 requirements

**Quick verification:**
```bash
# Check files exist
ls -la LICENSE README.md

# Verify LICENSE is GPL v3
head -3 LICENSE | grep "GNU GENERAL PUBLIC LICENSE"
head -3 LICENSE | grep "Version 3"

# Check size (should be ~35KB)
wc -c LICENSE

# Check README badge
grep -i "gpl" README.md
```

---

**Document Version:** 1.0
**Last Updated:** 2025-12-09
**Maintained By:** Dev-Nexus Project
**Questions?** See [DOCUMENTATION_STANDARDS.md](./DOCUMENTATION_STANDARDS.md) or open an issue.
