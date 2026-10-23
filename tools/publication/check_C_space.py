"""Root pre-write eligibility check. Fixed C: reserve; default performs no I/O."""
import argparse
import datetime
import json
import re
import shutil

DRIVE = "C:/"
RESERVE_BYTES = 107374182400


def positive_budget(value):
    if not isinstance(value, str) or re.fullmatch(r"[0-9]+", value) is None:
        raise argparse.ArgumentTypeError("peak budget must be a positive integer number of bytes")
    try:
        amount = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("invalid integer byte budget") from exc
    if amount < 1:
        raise argparse.ArgumentTypeError("peak budget must be at least 1 byte")
    return amount


def assess(free_bytes, peak_additional_bytes):
    if type(free_bytes) is not int or free_bytes < 0:
        raise ValueError("free bytes must be a nonnegative integer")
    if type(peak_additional_bytes) is not int or peak_additional_bytes < 1:
        raise ValueError("peak budget must be a positive integer")
    remaining = free_bytes - peak_additional_bytes
    return {
        "drive": DRIVE,
        "reserve_bytes": RESERVE_BYTES,
        "observed_free_bytes": free_bytes,
        "peak_additional_bytes": peak_additional_bytes,
        "free_minus_peak_bytes": remaining,
        "passed": remaining >= RESERVE_BYTES,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--peak-additional-bytes", type=positive_budget)
    args = parser.parse_args(argv)
    if not args.check:
        print(json.dumps({"inert": True, "filesystem_queries": 0, "writes": 0}))
        return 0
    if args.peak_additional_bytes is None:
        parser.error("--check requires an explicit --peak-additional-bytes budget")
    try:
        free_bytes = shutil.disk_usage(DRIVE).free
    except OSError as exc:
        print(json.dumps({"status": "HOLD", "drive": DRIVE,
                          "reserve_bytes": RESERVE_BYTES,
                          "reason": "C_SPACE_UNAVAILABLE", "error_type": type(exc).__name__}))
        return 2
    result = assess(free_bytes, args.peak_additional_bytes)
    result.update({
        "schema": "Root-C-prewrite-100GiB-eligibility/1",
        "observed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "PASS" if result["passed"] else "HOLD",
        "limitation": "Point-in-time check; does not reserve space or control other apps.",
        "permanent_free_space_guarantee": False,
        "writes": 0,
    })
    print(json.dumps(result, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
