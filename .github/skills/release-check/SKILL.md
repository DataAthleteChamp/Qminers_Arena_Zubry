---
name: release-check
description: Human-triggered preflight, reproduction, hash and manual Final-selection checklist for a single Arena strategy; never auto-uploads.
disable-model-invocation: true
---

Read [RELEASE](../../../docs/human/RELEASE.md).
Confirm <=1 MiB, Python 3.13, one public BaseStrategy subclass, allowed imports,
actual official-engine run and independent review. Local preflight is not the
complete server checker. Verify intended Final after a successful upload.
Keep rollback, receipts and all commits. No squash/rebase/amend/force-push or
Copilot attribution in commit messages; no automatic invitation/transfer/upload.
