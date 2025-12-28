---
topic: torchaudio-backends
status: complete
created: 2025-12-28
updated: 2025-12-28
---

# TorchAudio Backend Selection

## Summary

TorIO's FFmpeg extension fails to load on macOS due to missing RPATH
configuration for system FFmpeg dylibs. The solution is to configure torchaudio
to use the `soundfile` backend, which uses libsndfile and is more portable
across platforms.

## Context

The scribbulus diarization feature has this dependency chain:

```text
whisperx → pyannote-audio → torchaudio → torio
```

When pyannote-audio loads audio files, it triggers torchaudio which attempts to
load TorIO's FFmpeg extension. On macOS with Homebrew-installed FFmpeg, this
fails:

```text
OSError: dlopen(.../libtorio_ffmpeg6.so, 0x0006):
  Library not loaded: @rpath/libavutil.58.dylib
  Referenced from: .../libtorio_ffmpeg6.so
  Reason: no LC_RPATH's found
```

The error cascades through FFmpeg versions 6, 5, and 4, all failing with the
same RPATH issue. This happens because:

1. TorIO compiles FFmpeg extensions with `@rpath` references
2. The extensions expect FFmpeg dylibs to be discoverable via RPATH
3. Homebrew FFmpeg doesn't configure RPATH for third-party libraries
4. The dylibs exist on the system but aren't found at runtime

## Options Evaluated

### Option 1: Fix FFmpeg RPATH

Configure the system or environment to make FFmpeg dylibs discoverable.

**Approaches:**

- Set `DYLD_LIBRARY_PATH` to include Homebrew's lib directory
- Rebuild torio with correct RPATH
- Use `install_name_tool` to fix the .so files

**Pros:**

- Uses FFmpeg backend (potentially more features)
- No Python dependency changes

**Cons:**

- Complex and fragile across macOS versions
- `DYLD_LIBRARY_PATH` is stripped in some contexts (SIP)
- Different fix needed per platform
- May break on torio/torchaudio updates

### Option 2: Use soundfile Backend

Configure torchaudio to use the soundfile backend instead of FFmpeg.

**Pros:**

- Simple configuration change
- libsndfile is portable and well-supported
- Works reliably on macOS, Linux, Windows
- soundfile Python package handles native library discovery
- Supported by torchaudio as an official backend

**Cons:**

- Fewer supported formats than FFmpeg
- Additional Python dependency (soundfile)
- Requires libsndfile system library

### Option 3: Use sox_io Backend

Configure torchaudio to use the sox_io backend.

**Pros:**

- Alternative to FFmpeg
- Good format support

**Cons:**

- Requires SoX library installation
- Less portable than soundfile
- Not as widely available on all platforms

## Comparison

| Criteria              | Fix RPATH | soundfile | sox_io |
| --------------------- | --------- | --------- | ------ |
| Implementation effort | High      | Low       | Medium |
| Portability           | Low       | High      | Medium |
| Maintenance burden    | High      | Low       | Medium |
| Format support        | Best      | Good      | Good   |
| Reliability           | Low       | High      | Medium |

**Format support comparison:**

| Format | FFmpeg | soundfile | sox_io |
| ------ | ------ | --------- | ------ |
| WAV    | Yes    | Yes       | Yes    |
| FLAC   | Yes    | Yes       | Yes    |
| OGG    | Yes    | Yes       | Yes    |
| MP3    | Yes    | No\*      | Yes    |
| AAC    | Yes    | No        | No     |

\*soundfile can read MP3 with libsndfile 1.1.0+ and libmpg123

For diarization, the audio is typically preprocessed WAV, so soundfile's format
support is sufficient.

## Recommendation

### Use Option 2: soundfile backend

1. Add `soundfile>=0.13.0` as a required dependency
2. Configure torchaudio to use soundfile backend at startup
3. Fall back to sox_io if soundfile not available
4. Install libsndfile system library via package manager

Implementation:

```python
import os
os.environ.setdefault("TORCHAUDIO_USE_BACKEND_DISPATCHER", "1")

import torchaudio
backends = torchaudio.list_audio_backends()
if "soundfile" in backends:
    torchaudio.set_audio_backend("soundfile")
elif "sox_io" in backends:
    torchaudio.set_audio_backend("sox_io")
```

System library installation:

- macOS: `brew install libsndfile`
- Ubuntu/Debian: `apt install libsndfile1`
- Fedora: `dnf install libsndfile`

## References

- [TorchAudio Backends Documentation](https://pytorch.org/audio/stable/backend.html)
- [soundfile Python Package](https://python-soundfile.readthedocs.io/)
- [libsndfile](http://www.mega-nerd.com/libsndfile/)

## Related Documents

- [Task: Transcribe Command Fixes](../task/transcribe-command-fixes.plan.md)
- [Research: FFmpeg Audio Extraction](./ffmpeg-audio-extraction.md)
- [Feature: Diarization](../feature/diarization.md)
