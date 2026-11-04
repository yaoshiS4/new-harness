# API Contract First Guideline

**Trigger**: Task creates or modifies APIs

## Rules
1. Define API contract BEFORE implementation
2. Contract includes: endpoint, method, request, response, errors
3. Contract is versioned
4. Breaking changes require migration plan
5. Backward compatibility maintained for 1 version

## Contract Format
```yaml
endpoint: /api/v1/resource
method: GET/POST/PUT/DELETE
request:
  headers: { }
  body: { }
response:
  200: { }
  400: { }
  404: { }
  500: { }
errors:
  - code: ERROR_CODE
    message: Human readable
    resolution: How to fix
```
