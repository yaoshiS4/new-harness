# Experience Capsule: widget_weather_sync_deep_link

```yaml
experience_capsule:
  id: widget_weather_sync_deep_link
  layer: general
  verdict: helped
  confidence: high
  cue: widget weather lifecycle android deep link sync open-meteo
  created_at: 2026-10-20T14:19:57.419862+00:00
  status: active
```

## Cue
widget weather lifecycle android deep link sync open-meteo

## Lesson
Persist native widget weather across cold-start syncs using snapshotLock; interpolate hourly forecasts offline in WidgetUpdateHelper; trigger deep-link forced refetch with synchronous inFlight abort cleanup to prevent stale weather UI.

## Causal Evidence
45/45 mobile test suites pass, 487/487 tests pass, 9/9 core suites pass; 5 APK variants rebuilt cleanly.

## Verification & Metrics
- Causal Verdict: helped
- Confidence: high
- Metrics:
```json
{}
```
