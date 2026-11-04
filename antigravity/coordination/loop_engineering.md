# Governed Loop Engineering Specification (LEAF)

<!-- Reference: arXiv:2607.00038 -->

## 1. Loop Anatomy
Every autonomous agent execution cycle is structured as a governed loop:
1. **Trigger**: Specific task contract, test failure, or escalation.
2. **Goal**: Concrete acceptance criteria with explicit file boundary.
3. **Verification**: Air-gapped test execution with non-zero exit code check.
4. **Stopping Rule**: Success, max attempts (3), stagnation (2), or token limit.
5. **Memory**: Validated outcome capture in `codex_knowledge`.

## 2. Generator-Evaluator Separation (D12)
- Builders do NOT evaluate their own success.
- Test outcomes are read from fresh command execution, not assumed.
- Any discrepancy between claimed test state and actual exit code is an immediate failure.

## 3. Oscillation & Thrashing Circuit Breakers (D11)
- If attempt $N$ is structurally similar to attempt $N-2$ with the same failing symptom, abort loop immediately.
- Capture diagnostic error trace and route to `Role: "debugger"` or escalate to human.
- Do not blindly retry syntax or import variations more than twice.
