# wafflebot

## An empty voice-memos directory is the normal state

```
NoVoiceMemosFoundError: No voice memos found in data/voice-memos
```

This is what a run with nothing to do looks like. Voice memos arrive a few
times a week, so most runs find none. It is not a fault, and it does not need
investigating or fixing.

The pipeline runs daily at 04:00 on `topher-homelab` as
`homelab-run-wafflebot.service`. The script exits non-zero on this path, so on
days with no memos the unit lands in `failed` state. Treat a `failed`
wafflebot unit as uninformative until the exit code distinguishes "nothing to
do" from a real failure.

The Healthcheck.io ping is gated to the staging run on purpose: prod only does
work when there are new memos, so the nightly staging run is the canary for
both.
