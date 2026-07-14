#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for finish-close.py (acp-ajudd#103 / #107).

Run with a plain interpreter from anywhere:

    python test-finish-close.py         # or python3

Guards the recurring partial-close class that #107 fixed. Grouped by the fix each
case protects:

  FIX 0     — verify_close re-reads every surface and reports each miss (incl. the
              #102-class missing-[DONE]) before the close may exit 0.
  Defect 1  — a UTF-8 payload (em-dash) survives the Git-Bash cp1252 stdin locale,
              driven through the real CLI via subprocess (the load-bearing I/O path).
  Defect 2  — reworded history/worklog re-run rows dedup on a stable key, not text.
  Defect 3  — compute_archive_stamp resolves the entry by its `## <id>` header, not
              the nearest CONSUMED line. The four fixtures the entry names explicitly:
              stamp-after-##, stamp-before-## (the #102 regression), no-CONSUMED-yet,
              and idempotent re-run on an already-[DONE] block (true no-op).

Exit status: 0 if every case passes, 1 otherwise (CI-friendly).
"""
import importlib.util
import os
import re
import subprocess
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DASH = "—"   # em-dash — the char that mangled under cp1252 (Defect 1)
ARROW = "→"  # → the CONSUMED arrow variant

HERE = os.path.dirname(os.path.abspath(__file__))
FC_PATH = os.path.join(HERE, "finish-close.py")

_spec = importlib.util.spec_from_file_location("finish_close", FC_PATH)
fc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fc)

_passed = 0
_failed = 0


def ok(cond, label):
    global _passed, _failed
    if cond:
        _passed += 1
        print("  PASS  " + label)
    else:
        _failed += 1
        print("  FAIL  " + label)


def section(title):
    print("\n== %s ==" % title)


def _write(path, content):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
    return path


# ---------------------------------------------------------------------------
# Defect 3 — header-bounded archive-block resolution (the four named fixtures).
# ---------------------------------------------------------------------------

def test_defect3():
    section("Defect 3: compute_archive_stamp header-bounded resolution")

    # Fixture 1 — stamp-AFTER-## (newer convention, e.g. #97): CONSUMED below header.
    after = (
        "## acp-ajudd#97 " + DASH + " title\n"
        "> [type: work]\n"
        "body\n"
        "[CONSUMED 2026-07-14 -> session close-safety-cue]\n"
    )
    nt, note, ed = fc.compute_archive_stamp(after, "acp-ajudd#97", "2026-07-14", "v1.83.0")
    _, bs, be = fc._locate_entry(nt.split("\n"), "acp-ajudd#97")
    ok(ed and any(l.startswith("[DONE") for l in nt.split("\n")[bs:be]),
       "stamp-after-##: [DONE] inserted in the #97 block")

    # Fixture 2 — stamp-BEFORE-## (older convention, THE #102 REGRESSION): CONSUMED
    # sits ABOVE the header, and the PRIOR entry (#97) already carries [DONE]. Keying
    # off the nearest CONSUMED line resolved to #97's block and false-positived
    # "already stamped", dropping #102's real [DONE]. Header-bounding must not.
    before = (
        "## acp-ajudd#97 " + DASH + " prev\n"
        "body97\n"
        "[CONSUMED 2026-07-14 -> session close-safety-cue]\n"
        "[DONE 2026-07-14 " + DASH + " shipped v1.83.0]\n"
        "\n"
        "[CONSUMED 2026-07-14 " + ARROW + " session inbox-per-item-storage]\n"
        "## acp-ajudd#102 " + DASH + " title102\n"
        "> [type: work]\n"
        "body102\n"
    )
    nt2, note2, ed2 = fc.compute_archive_stamp(before, "acp-ajudd#102", "2026-07-14", "v2.0.0")
    lines2 = nt2.split("\n")
    _, b2s, b2e = fc._locate_entry(lines2, "acp-ajudd#102")
    ok(ed2 and "stamped" in note2 and any(l.startswith("[DONE") for l in lines2[b2s:b2e]),
       "stamp-before-## (#102): [DONE] lands in #102's block, not a false no-op")
    _, b97s, b97e = fc._locate_entry(lines2, "acp-ajudd#97")
    ok(sum(1 for l in lines2[b97s:b97e] if l.startswith("[DONE")) == 1,
       "stamp-before-##: #97's block keeps exactly one [DONE] (no bleed/double-stamp)")
    idx_hdr = next(i for i, l in enumerate(lines2) if l.startswith("## acp-ajudd#102"))
    idx_con = next(i for i, l in enumerate(lines2) if "inbox-per-item-storage" in l)
    ok(idx_con > idx_hdr, "stamp-before-##: target's stray CONSUMED self-heals below its header")

    # Fixture 3 — no CONSUMED yet (header only): [DONE] goes right after the header.
    nocon = "## acp-ajudd#110 " + DASH + " t\n> [type: work]\nbody\n"
    nt3, note3, ed3 = fc.compute_archive_stamp(nocon, "acp-ajudd#110", "2026-07-14", "n")
    l3 = nt3.split("\n")
    ok(ed3 and l3[1].startswith("[DONE"), "no-CONSUMED-yet: [DONE] inserted right after the header")

    # Fixture 4 — idempotent re-run on an already-[DONE] block: true no-op.
    nt4, note4, ed4 = fc.compute_archive_stamp(nt, "acp-ajudd#97", "2026-07-14", "again")
    ok(nt4 == nt and ed4 and "no-op" in note4,
       "already-[DONE]: true no-op (text unchanged), expect_done stays True")

    # Guard — header missing is a soft anomaly (surfaced, not a false stamp).
    nt5, note5, ed5 = fc.compute_archive_stamp(after, "acp-ajudd#999", "2026-07-14", "x")
    ok(nt5 == after and not ed5 and "NOT stamped" in note5,
       "missing header: soft note + expect_done False (close not blocked)")

    # Guard — id boundary: #10 must never resolve to #102.
    multi = ("## acp-ajudd#102 " + DASH + " a\nbody\n"
             "## acp-ajudd#10 " + DASH + " b\nbody\n")
    h10 = fc._locate_entry(multi.split("\n"), "acp-ajudd#10")[0]
    ok(multi.split("\n")[h10].startswith("## acp-ajudd#10 "), "id boundary: #10 != #102")


# ---------------------------------------------------------------------------
# Defect 3-ii — one-time CONSUMED-placement migration.
# ---------------------------------------------------------------------------

def test_migration():
    section("Defect 3-ii: normalize_consumed_placement (one-time migration)")
    before = (
        "## acp-ajudd#97 " + DASH + " prev\nbody97\n"
        "[CONSUMED 2026-07-14 -> session close-safety-cue]\n"
        "[DONE 2026-07-14 " + DASH + " shipped]\n\n"
        "[CONSUMED 2026-07-14 " + ARROW + " session inbox-per-item-storage]\n"
        "## acp-ajudd#102 " + DASH + " title102\nbody102\n"
    )
    mig = fc.normalize_consumed_placement(before)
    ml = mig.split("\n")
    ih = next(i for i, l in enumerate(ml) if l.startswith("## acp-ajudd#102"))
    ic = next(i for i, l in enumerate(ml) if "inbox-per-item-storage" in l)
    ok(ic == ih + 1, "migration: stray stamp-before-## CONSUMED moved directly below its header")
    ok(fc.normalize_consumed_placement(mig) == mig, "migration: idempotent (re-run is a no-op)")
    ok("[CONSUMED 2026-07-14 -> session close-safety-cue]" in mig,
       "migration: already-correct (blank-separated) CONSUMED left untouched")
    # content-preserving: only reorders, never adds/removes a line
    ok(sorted(before.split("\n")) == sorted(mig.split("\n")),
       "migration: line-set identical (pure reorder)")


# ---------------------------------------------------------------------------
# Defect 2 — stable-key dedup for reworded history/worklog re-runs.
# ---------------------------------------------------------------------------

def test_defect2():
    section("Defect 2: stable-key dedup (compute_append)")
    hist_re = re.compile(r"^\[2026-07-14")
    wl_re = re.compile(r"^##\s")

    hist = "[2026-07-14 @ajudd] finish-close-harden " + DASH + " original wording.\n"
    reworded = "[2026-07-14 @ajudd] finish-close-harden " + DASH + " COMPLETELY different words."
    _, changed = fc.compute_append(hist, reworded, hist_re, "finish-close-harden")
    ok(not changed, "history: reworded same-session re-run line dedups (stable key)")

    other = "[2026-07-14 @ajudd] other-session " + DASH + " x"
    _, changed2 = fc.compute_append(hist, other, hist_re, "other-session")
    ok(changed2, "history: a different session on the same date still appends")

    wl = "## 16:39 " + DASH + " finish-close-harden\n\n**Accomplished:** a\n"
    wl_rw = "## 16:41 " + DASH + " finish-close-harden\n\n**Accomplished:** reworded b"
    _, wc = fc.compute_append(wl, wl_rw, wl_re, "finish-close-harden")
    ok(not wc, "worklog: reworded same-session block dedups (header + name key)")

    wl2 = "## 1 " + DASH + " finish-close-harden-v2\n\nx"
    _, wc2 = fc.compute_append(wl2, "## 2 " + DASH + " finish-close-harden\n\ny",
                               wl_re, "finish-close-harden")
    ok(wc2, "worklog: name matched as a whole token (harden != harden-v2)")


# ---------------------------------------------------------------------------
# FIX 0 — verify_close catches every partial (incl. the #102-class missing [DONE]).
# ---------------------------------------------------------------------------

def test_fix0_verify():
    section("FIX 0: verify_close read-back catches partials")
    d = tempfile.mkdtemp()

    def paths_with(**over):
        base = dict(
            session=_write(os.path.join(d, "s.md"),
                           "---\ntype: plugin\nstatus: completed\n---\n- **Status:** completed\n"),
            index=_write(os.path.join(d, "_index.md"),
                         "# i\nfixsess | @a | 2026-07-14 | @a | 2026-07-14 | completed | " + DASH + "\n"),
            active=os.path.join(d, "_active"),  # absent = cleared
            history=_write(os.path.join(d, "_history.md"),
                           "[2026-07-14 @ajudd] fixsess " + DASH + " did it.\n"),
            worklog=_write(os.path.join(d, "wl.md"), "## 12:00 " + DASH + " fixsess\n\nx\n"),
            archive=_write(os.path.join(d, "_arc.md"),
                           "## acp-ajudd#200 " + DASH + " t\n"
                           "[CONSUMED 2026-07-14 -> session fixsess]\n"
                           "[DONE 2026-07-14 " + DASH + " y]\n"),
        )
        base.update(over)
        return base

    good = paths_with()
    ok(fc.verify_close(good, "fixsess", "acp-ajudd#200", "2026-07-14",
                       True, True, True, True) == [],
       "all six surfaces confirmed: no failures")

    bad_body = _write(os.path.join(d, "s_bad.md"),
                      "---\ntype: plugin\nstatus: completed\n---\n- **Status:** active\n")
    f = fc.verify_close(paths_with(session=bad_body), "fixsess", "acp-ajudd#200",
                        "2026-07-14", True, True, True, True)
    ok(any("body" in x for x in f), "body Status not completed -> caught")

    bad_idx = _write(os.path.join(d, "_idx_bad.md"),
                     "# i\nfixsess | @a | 2026-07-14 | @a | 2026-07-14 | active | -\n")
    f = fc.verify_close(paths_with(index=bad_idx), "fixsess", "acp-ajudd#200",
                        "2026-07-14", True, True, True, True)
    ok(any("_index" in x for x in f), "_index row not completed -> caught")

    active_present = _write(os.path.join(d, "_active_live"), "fixsess")
    f = fc.verify_close(paths_with(active=active_present), "fixsess", "acp-ajudd#200",
                        "2026-07-14", True, True, True, True)
    ok(any("_active" in x for x in f), "_active still present -> caught")

    # THE #102-CLASS: [DONE] missing from the target block but expect_done=True.
    no_done = _write(os.path.join(d, "_arc_nodone.md"),
                     "## acp-ajudd#200 " + DASH + " t\n[CONSUMED 2026-07-14 -> session fixsess]\n")
    f = fc.verify_close(paths_with(archive=no_done), "fixsess", "acp-ajudd#200",
                        "2026-07-14", True, True, True, True)
    ok(any("[DONE]" in x for x in f), "missing [DONE] (the #102 partial) -> caught")

    empty_hist = _write(os.path.join(d, "_hist_empty.md"), "# empty\n")
    f = fc.verify_close(paths_with(history=empty_hist), "fixsess", "acp-ajudd#200",
                        "2026-07-14", True, True, True, True)
    ok(any("_history" in x for x in f), "missing history line -> caught")

    # A bare session (expect_done False) does not require an archive [DONE].
    f = fc.verify_close(paths_with(archive=no_done), "fixsess", "",
                        "2026-07-14", True, True, True, False)
    ok(not any("DONE" in x for x in f), "expect_done False: archive [DONE] not required")


# ---------------------------------------------------------------------------
# Defect 1 — drive a REAL close through the CLI so the em-dash payload crosses the
# actual stdin byte boundary (the path that mangled under Git-Bash cp1252).
# ---------------------------------------------------------------------------

def test_defect1_integration():
    section("Defect 1 + FIX 0: real CLI close, em-dash payload, self-verified")
    d = tempfile.mkdtemp()
    sroot = os.path.join(d, "sroot")
    sess_slug_dir = os.path.join(d, "sessroot", "testslug")
    os.makedirs(sroot)
    os.makedirs(sess_slug_dir)

    _write(os.path.join(sroot, "fixsess.md"),
           "---\nupdated: 2026-07-14\ntype: plugin\nstatus: active\n---\n"
           "# Session State " + DASH + " fixsess\n- **Status:** active\n")
    _write(os.path.join(sroot, "_index.md"),
           "# Index\nfixsess | @ajudd | 2026-07-14 | @ajudd | 2026-07-14 | active | -\n")
    # stamp-before-## archive entry so the CLI exercises Defect 3 too.
    _write(os.path.join(sroot, "_inbox_archive.md"),
           "## acp-ajudd#97 " + DASH + " prev\nbody\n"
           "[CONSUMED 2026-07-14 -> session close-safety-cue]\n"
           "[DONE 2026-07-14 " + DASH + " shipped]\n\n"
           "[CONSUMED 2026-07-14 " + ARROW + " session fixsess]\n"
           "## acp-ajudd#200 " + DASH + " title200\n> [type: work]\nbody200\n")
    _write(os.path.join(sess_slug_dir, "_active"), "fixsess")
    worklog = os.path.join(d, "wl", "2026-07-14.md")

    payload = (
        '{"history_line": "[2026-07-14 @ajudd] fixsess ' + DASH +
        ' shipped acp-ajudd#200 with an em-dash ' + DASH + ' and more.", '
        '"worklog_entry": "## 12:00 ' + DASH + ' fixsess\\n\\n**Accomplished:** did it ' + DASH +
        ' cleanly.\\n\\n**Open items:** none", '
        '"done_note": "shipped v2.1.0 ' + DASH + ' em-dash survives"}'
    )

    def run(pl):
        return subprocess.run(
            [sys.executable, FC_PATH,
             "--session-root", sroot, "--slug", "testslug", "--name", "fixsess",
             "--type", "plugin", "--date", "2026-07-14", "--handle", "ajudd",
             "--item-id", "acp-ajudd#200", "--sessions-root", os.path.join(d, "sessroot"),
             "--worklog-path", worklog],
            input=pl.encode("utf-8"), capture_output=True)

    r = run(payload)
    ok(r.returncode == 0, "CLI close exits 0 (self-verified) with an em-dash payload")

    arc = open(os.path.join(sroot, "_inbox_archive.md"), encoding="utf-8").read()
    hist = open(os.path.join(sroot, "_history.md"), encoding="utf-8").read()
    ok(DASH in hist and "�" not in hist and "â" not in hist,
       "Defect 1: em-dash survived intact in _history.md (no mojibake / lone surrogate)")
    l = arc.split("\n")
    _, b2s, b2e = fc._locate_entry(l, "acp-ajudd#200")
    ok(any(x.startswith("[DONE") for x in l[b2s:b2e]), "Defect 3: [DONE] in #200's block via CLI")
    _, b97s, b97e = fc._locate_entry(l, "acp-ajudd#97")
    ok(sum(1 for x in l[b97s:b97e] if x.startswith("[DONE")) == 1, "Defect 3: #97 not double-stamped")

    # Reworded idempotent re-run: converges, dedups, exits 0 self-verified (Defect 2).
    _write(os.path.join(sess_slug_dir, "_active"), "fixsess")  # simulate a retry
    reworded = payload.replace("shipped acp-ajudd#200 with an em-dash " + DASH + " and more.",
                               "TOTALLY reworded second-pass line.")
    r2 = run(reworded)
    ok(r2.returncode == 0, "reworded re-run: exits 0 (idempotent + self-verified)")
    hist2 = open(os.path.join(sroot, "_history.md"), encoding="utf-8").read()
    ok(hist2.count("] fixsess ") == 1, "Defect 2: reworded re-run did NOT duplicate the history row")
    wl2 = open(worklog, encoding="utf-8").read()
    ok(wl2.count(DASH + " fixsess") == 1, "Defect 2: reworded re-run did NOT duplicate the worklog block")


def main():
    test_defect3()
    test_migration()
    test_defect2()
    test_fix0_verify()
    test_defect1_integration()
    print("\n%d passed, %d failed" % (_passed, _failed))
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
