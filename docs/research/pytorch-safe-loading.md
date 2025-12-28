---
topic: pytorch-safe-loading
status: complete
created: 2025-12-28
updated: 2025-12-28
---

# PyTorch Safe Loading Compatibility

## Summary

PyTorch 2.6+ changed `torch.load()` default from `weights_only=False` to
`weights_only=True` for security. This breaks loading pyannote model
checkpoints which contain non-allowlisted types like `TorchVersion` and
OmegaConf `ListConfig`. The recommended workaround is setting the environment
variable `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1` when loading trusted HuggingFace
models.

## Context

The scribbulus diarization feature depends on:

- whisperx (speaker diarization orchestration)
- pyannote-audio (diarization models from HuggingFace)
- PyTorch (model loading and inference)

When PyTorch 2.6 was released, it changed the default behavior of `torch.load()`
to require explicit allowlisting of non-tensor types for security reasons. This
is a good security practice for untrusted checkpoints, but breaks loading
official HuggingFace pyannote models.

Error observed:

```text
WeightsUnpickler error: Unsupported global:
  GLOBAL torch.torch_version.TorchVersion was not an allowed global by default.
```

## Options Evaluated

### Option 1: Downgrade PyTorch

**Pros:**

- Simple, no code changes needed
- Avoids the issue entirely

**Cons:**

- Loses PyTorch 2.8+ features and performance improvements
- Not viable for projects requiring modern PyTorch
- Creates version conflicts with other dependencies

### Option 2: Manual `add_safe_globals()`

**Pros:**

- Fine-grained control over allowlisted types
- More explicit about security decisions

**Cons:**

- Requires tracking all types used by pyannote checkpoints
- Types can change between model versions
- Complex implementation with multiple classes to allowlist
- Requires maintenance as dependencies update

### Option 3: `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1` Environment Variable

**Pros:**

- Simple, single line of code
- Official PyTorch mechanism
- Community-recommended solution for trusted sources
- No need to track specific types

**Cons:**

- Disables safe loading entirely for that process
- Should only be used with trusted model sources

### Option 4: Wait for Upstream Fix

**Pros:**

- No local workarounds needed
- Proper fix from library maintainers

**Cons:**

- whisperX issue still open (as of Dec 2025)
- pyannote-audio 4.x released but whisperx hasn't updated
- Blocks users indefinitely

## Comparison

| Criteria              | Downgrade | add_safe_globals | Env Var | Wait |
| --------------------- | --------- | ---------------- | ------- | ---- |
| Implementation effort | None      | High             | Low     | None |
| Maintenance burden    | High      | High             | Low     | None |
| Security impact       | Medium    | Low              | Medium  | None |
| User impact           | High      | None             | None    | High |
| Viability             | No        | Yes              | Yes     | No   |

## Recommendation

### Use Option 3: Environment variable workaround

Set `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1` before loading diarization models.
This is:

1. The community-recommended solution per whisperX#1304
2. Safe for our use case (loading official HuggingFace pyannote models)
3. Simple to implement and maintain
4. Easy to remove when whisperx updates to pyannote-audio 4.x

Implementation:

```python
# Before loading diarization models
os.environ.setdefault("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "1")
```

## References

- [pyannote-audio#1908](https://github.com/pyannote/pyannote-audio/issues/1908)

  - Status: CLOSED
  - pyannote-audio 4.x released with PyTorch 2.8+ compatibility

- [whisperX#1304](https://github.com/m-bain/whisperX/issues/1304)

  - Status: OPEN
  - Environment variable workaround recommended by community

- [PyTorch torch.load documentation](https://pytorch.org/docs/stable/generated/torch.load.html)
  - Documents `weights_only` parameter and safe loading behavior

## Related Documents

- [Task: Transcribe Command Fixes](../task/transcribe-command-fixes.plan.md)
- [Feature: Diarization](../feature/diarization.md)
