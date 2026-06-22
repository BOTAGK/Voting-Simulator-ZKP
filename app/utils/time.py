from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def is_within_datetime_window(
    starts_at: datetime | None,
    ends_at: datetime | None,
    now: datetime | None = None,
) -> bool:
    current_time = as_utc(now or utc_now())

    if starts_at is not None and current_time < as_utc(starts_at):
        return False

    if ends_at is not None and current_time > as_utc(ends_at):
        return False

    return True
