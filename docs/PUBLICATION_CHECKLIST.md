# Publication Checklist

Before the first public source-code release:

- [ ] Decide whether to add a software license before granting reuse rights.
- [ ] Confirm the repository name and description.
- [ ] Run `pytest -q`.
- [ ] Run the complete synthetic example.
- [ ] Search for credentials, account numbers, private URLs, user names, and VPS paths.
- [ ] Confirm no platform-specific production strategy code is included.
- [ ] Confirm no private market data is included.
- [ ] Confirm example results are generated only from synthetic data.
- [ ] Review third-party license, terms, attribution, and redistribution requirements.
- [ ] Scan public-facing documentation/templates/examples for unnecessary third-party brand or product names; use source-neutral categories where possible.
- [ ] Tag the first release only after the public commit is final.

A license is intentionally not preselected in v0.1.0. Licensing should remain a separate, deliberate publication decision.
