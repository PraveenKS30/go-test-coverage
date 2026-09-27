#!/usr/bin/env python3
"""
Generate table-driven test skeletons for Go functions — single-function mode
or batch mode across an entire package or repo.

Deliberately does NOT invent expected values in any mode — every case is
emitted with a TODO marker (see anti-patterns.md: no guessed assertions).

Usage:
    # Single function (original mode)
    python3 scaffold_test.py path/to/file.go FunctionName

    # Batch mode: scan one directory for every exported func missing a test
    python3 scaffold_test.py path/to/package_dir --all

    # Batch mode: scan an entire repo (all .go files, all packages)
    python3 scaffold_test.py path/to/repo --all --recursive

Batch mode reports, per function found, one of:
    SCAFFOLDED  - no existing Test<Func> found anywhere; skeleton written
    HAS_TEST    - a Test<Func> already exists somewhere in the package; skipped
    SKIPPED     - unexported function (lowercase) or a main()/init(); skipped

This lets you point the script at a whole repo and get a full inventory of
test debt in one pass, instead of hunting function-by-function.
"""
import re
import sys
from pathlib import Path

FUNC_DECL_RE = re.compile(r"^func\s+([A-Za-z_]\w*)\s*\(([^)]*)\)\s*([^\{]*)\{", re.MULTILINE)
TEST_FUNC_RE = re.compile(r"^func\s+(Test\w+)\s*\(", re.MULTILINE)


def find_go_files(path: Path, recursive: bool):
    if path.is_file():
        return [path]
    pattern = "**/*.go" if recursive else "*.go"
    return [p for p in path.glob(pattern) if not p.name.endswith("_test.go")]


def find_test_files(directory: Path):
    return list(directory.glob("*_test.go"))


def existing_test_names(test_files) -> set:
    names = set()
    for tf in test_files:
        if tf.exists():
            names.update(TEST_FUNC_RE.findall(tf.read_text()))
    return names


def is_exported(name: str) -> bool:
    return name[0:1].isupper()


def get_package(source: str) -> str:
    m = re.search(r"^package\s+(\w+)", source, re.MULTILINE)
    return m.group(1) if m else "main"


def emit_skeleton(package: str, func_name: str, params: str, returns: str) -> str:
    has_error_return = "error" in returns
    return f'''package {package}

import (
\t"errors"
\t"testing"
)

// SCAFFOLD GENERATED — skeleton only. Fill every TODO with an
// independently-derived expected value (see references/anti-patterns.md).
// Do not paste the code's current output as the expected value.

func Test{func_name}(t *testing.T) {{
\ttests := []struct {{
\t\tname string
\t\t// TODO: one field per parameter: ({params})
{"\t\twantErr error" if has_error_return else "\t\t// no error return detected"}
\t\t// TODO: one field per non-error return value: ({returns})
\t}}{{
\t\t{{name: "TODO: happy path"}},
\t\t{{name: "TODO: boundary case at a branch threshold"}},
\t\t{{name: "TODO: edge case — zero/empty/nil input"}},
\t\t{{name: "TODO: error case"}},
\t\t// TODO: one case per remaining branch in {func_name}
\t}}

\tfor _, tt := range tests {{
\t\ttt := tt
\t\tt.Run(tt.name, func(t *testing.T) {{
\t\t\tt.Parallel()
\t\t\t// TODO: call {func_name}(...) and assert on the real return value(s)
\t\t\t_ = errors.New // placeholder; remove once wired up
\t\t}})
\t}}
}}
'''


def scaffold_one(go_file: Path, func_name: str) -> Path:
    source = go_file.read_text()
    package = get_package(source)
    match = re.search(rf"func\s+{re.escape(func_name)}\s*\(([^)]*)\)\s*([^\{{]*)\{{", source)
    params, returns = (m.strip() for m in match.groups()) if match else ("", "")

    out_path = go_file.parent / f"{go_file.stem}_{func_name.lower()}_scaffold_test.go"
    out_path.write_text(emit_skeleton(package, func_name, params, returns))
    return out_path


def batch_mode(target: Path, recursive: bool):
    go_files = find_go_files(target, recursive)
    if not go_files:
        print(f"No .go source files found under {target}")
        return

    by_dir = {}
    for gf in go_files:
        by_dir.setdefault(gf.parent, []).append(gf)

    total_found = total_scaffolded = total_has_test = total_skipped = 0

    for directory, files in sorted(by_dir.items()):
        test_files = find_test_files(directory)
        tested_names = existing_test_names(test_files)

        for gf in files:
            source = gf.read_text()
            for m in FUNC_DECL_RE.finditer(source):
                func_name = m.group(1)
                total_found += 1

                if not is_exported(func_name) or func_name in ("main", "init"):
                    print(f"  SKIPPED     {gf}:{func_name} (unexported/entrypoint)")
                    total_skipped += 1
                    continue

                if f"Test{func_name}" in tested_names:
                    print(f"  HAS_TEST    {gf}:{func_name}")
                    total_has_test += 1
                    continue

                out_path = scaffold_one(gf, func_name)
                print(f"  SCAFFOLDED  {gf}:{func_name} -> {out_path}")
                total_scaffolded += 1

    print()
    print(f"Summary: {total_found} functions found | "
          f"{total_scaffolded} scaffolded | {total_has_test} already tested | "
          f"{total_skipped} skipped (unexported)")
    if total_scaffolded:
        print(f"\n{total_scaffolded} skeleton file(s) written. None are finished tests — "
              "every TODO must be filled with a real, derived expected value "
              "before these count toward coverage.")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    recursive = "--recursive" in args
    batch = "--all" in args
    args = [a for a in args if a not in ("--recursive", "--all")]

    target = Path(args[0])

    if batch:
        batch_mode(target, recursive)
    else:
        if len(args) != 2:
            print(__doc__)
            sys.exit(1)
        func_name = args[1]
        out_path = scaffold_one(target, func_name)
        print(f"Wrote skeleton: {out_path}")


if __name__ == "__main__":
    main()
