# Proposal Schema (Blinded Ensemble Candidate)

```yaml
proposal:
  candidate_id: "Candidate A | Candidate B"   # Anonymized label for Blinded Candidate Selection
  owner: "<role>"                             # Hidden during blinded Oracle evaluation
  goal: "<concise objective>"
  allowed_files:
    - "<path/to/file>"
  oracle_custody_lease: "NONE | UPDATE_ASSERTIONS"
  verification_cmd: "<pytest / tsc command>"
  delta_behav: "<measured behavioral delta vs baseline>"
  tie_breaker_fallback: "KEEP_BASE"
  risks:
    - "<identified risk & mitigation>"
  next_action: "<MERGE_CANDIDATE | KEEP_BASE | REJECT>"
  oracle_required: true
```
