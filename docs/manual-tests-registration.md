# SmartCare registration manual checks

Not run manually yet. Replace “Not run” with Pass or Fail only after observing the MVP in your browser.

| Scenario | Steps | Expected result | Result |
|---|---|---|---|
| Valid registration | Register with a new email, name and six-character password | Account created; login works | Not run |
| Blank name | Submit a name containing spaces | “Full name is required”; no account created | Not run |
| Invalid email | Submit `invalid` as email | “Enter a valid email address” | Not run |
| Duplicate normalization | Register an email with spaces/capitals, then repeat without spaces | First succeeds; second returns “Email already registered” | Not run |
| Password boundary | Try five characters, then six, with separate valid addresses | Five rejected; six accepted | Not run |
| Access control | Log in as patient; request admin stats with bearer token | HTTP 403, “Admin access required” | Not run |
