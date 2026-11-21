"""Tests for the hr-orchestrate skills: SKILL.md structure and every bundled script.

Run: python -m unittest discover -s tests -v
"""
import csv
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")


def script(skill, name):
    return os.path.join(SKILLS, skill, "scripts", name)


def run(path, *args):
    p = subprocess.run([sys.executable, path] + list(args), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, p.stdout + p.stderr


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


GOOD_LOG = """## [2026-12-12T12:30:00Z] SESSION START

tool=Claude Code
model=claude-opus-5-5

## [2026-12-12T12:35:00Z] Read the contract

User Prompt (verbatim, secrets redacted):
Read AGENTS.md and summarise the output contract.

Agent Response Summary:
Read AGENTS.md and problem_statement.md and wrote docs/CONTRACT.md with three columns and 518 rows.

Actions:
* wrote docs/CONTRACT.md

Context:
tool=Claude Code
model=claude-opus-5-5
"""

STEPS = lambda *ops: json.dumps([{"step_no": i + 1, "system_id": "s", "resource_id": "r%d" % i, "operation": o}
                                 for i, o in enumerate(ops)], separators=(",", ":"))


class TestSkillFiles(unittest.TestCase):
    def test_frontmatter_and_links(self):
        dirs = sorted(d for d in os.listdir(SKILLS) if os.path.isdir(os.path.join(SKILLS, d)))
        self.assertEqual(len(dirs), 6, dirs)
        for d in dirs:
            path = os.path.join(SKILLS, d, "SKILL.md")
            text = open(path, encoding="utf-8").read()
            m = re.match(r"^---\nname: (.+)\ndescription: (.+)\n---\n", text)
            self.assertIsNotNone(m, "%s: bad frontmatter" % d)
            self.assertEqual(m.group(1).strip(), d)
            self.assertLessEqual(len(m.group(2)), 1024, d)
            self.assertLess(len(text.splitlines()), 500, d)
            for ref in set(re.findall(r"`((?:references|scripts)/[A-Za-z0-9_\-./]+)`", text)):
                self.assertTrue(os.path.exists(os.path.join(SKILLS, d, ref)), "%s links missing %s" % (d, ref))

    def test_scripts_have_help(self):
        for d in os.listdir(SKILLS):
            sd = os.path.join(SKILLS, d, "scripts")
            if not os.path.isdir(sd):
                continue
            for f in os.listdir(sd):
                if f.endswith(".py"):
                    code, out = run(os.path.join(sd, f), "--help")
                    self.assertEqual(code, 0, "%s/%s --help failed: %s" % (d, f, out))


class TestKickoff(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_check_log_good(self):
        p = os.path.join(self.d, "log.txt")
        open(p, "w", encoding="utf-8").write(GOOD_LOG)
        code, out = run(script("hr-orchestrate-kickoff", "check_log.py"), p, "--expect-tool", "Claude Code",
                        "--expect-model", "claude-opus-5-5", "--profile", "oct26")
        self.assertEqual(code, 0, out)

    def test_check_log_bad(self):
        bad = GOOD_LOG.replace("tool=Claude Code\nmodel=claude-opus-5-5\n\n## [2026-12-12T12:35",
                               "tool=<harness>\nmodel=Claude\n\n## [2026-12-12T12:35")
        bad += "\nkey sk-ant-api03-abcdefghijklmnopqrstuvwxyz\n"
        p = os.path.join(self.d, "log.txt")
        open(p, "w", encoding="utf-8").write(bad)
        code, out = run(script("hr-orchestrate-kickoff", "check_log.py"), p, "--json")
        self.assertEqual(code, 1)
        msgs = " ".join(r["message"] for r in json.loads(out)["results"])
        self.assertIn("placeholder", msgs)
        self.assertIn("model family", msgs)
        self.assertIn("secret", msgs)

    def test_contract_extract(self):
        open(os.path.join(self.d, "AGENTS.md"), "w", encoding="utf-8").write(
            "# Rules\n\nYou must write `output.csv` at the repo root.\n\n```text\ncase_id,status,steps_json\n```\n"
            "Allowed: `A`, `B`, `C`\nSubmit at https://example.com/challenge\n")
        code, out = run(script("hr-orchestrate-kickoff", "contract_extract.py"), self.d)
        self.assertEqual(code, 0, out)
        for s in ("case_id,status,steps_json", "`output.csv`", "https://example.com/challenge", "AGENTS.md:3"):
            self.assertIn(s, out)

    def test_profile_data(self):
        a = os.path.join(self.d, "sample_out.csv")
        b = os.path.join(self.d, "template.csv")
        write_csv(a, ["id", "status", "steps"], [["1", "OK", STEPS("X")], ["2", "OK", STEPS("Y")], ["3", "BAD", "[]"]])
        write_csv(b, ["id", "steps", "status"], [])
        code, out = run(script("hr-orchestrate-kickoff", "profile_data.py"), a, b, "--id-col", "id")
        self.assertEqual(code, 0, out)
        self.assertIn("likely enum", out)
        self.assertIn("JSON column", out)
        self.assertIn("DIFFERENT ORDER", out)


class TestBuild(unittest.TestCase):
    def test_usage_report(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "usage.jsonl")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(json.dumps({"run_id": "r1", "row_id": "a", "provider": "anthropic", "model": "m",
                                     "input_tokens": 1000000, "output_tokens": 100000, "cached": False}) + "\n")
                fh.write(json.dumps({"run_id": "r1", "row_id": "b", "provider": "anthropic", "model": "m",
                                     "input_tokens": 1000000, "output_tokens": 100000, "cached": True}) + "\n")
                fh.write(json.dumps({"run_id": "r0", "row_id": "a", "model": "m", "input_tokens": 5}) + "\n")
            out_md = os.path.join(d, "usage_report.md")
            code, out = run(script("hr-orchestrate-build", "usage_report.py"), p, "--run-id", "r1",
                            "--price", "m=3:15", "--out", out_md)
            self.assertEqual(code, 0, out)
            md = open(out_md, encoding="utf-8").read()
            self.assertIn("**$9.0000**", md)          # 2M in * 3 + 0.2M out * 15
            self.assertIn("| Billed est. cost | $4.5000 |", md)
            self.assertIn("| Est. cost per request | $4.5000 |", md)


class TestTestFix(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        self.d = d
        hdr = ["id", "status", "steps"]
        self.exp = os.path.join(d, "expected.csv")
        write_csv(self.exp, hdr, [["1", "OK", STEPS("A", "B")], ["2", "BAD", STEPS("C")], ["3", "OK", STEPS("D")]])
        self.before = os.path.join(d, "before.csv")
        write_csv(self.before, hdr, [["1", "BAD", STEPS("A", "B")], ["2", "BAD", STEPS("C")], ["3", "OK", STEPS("D")]])
        self.after = os.path.join(d, "after.csv")
        write_csv(self.after, hdr, [["1", "OK", STEPS("A", "B")], ["2", "BAD", STEPS("C")], ["3", "OK", STEPS("D")]])
        self.worse = os.path.join(d, "worse.csv")
        write_csv(self.worse, hdr, [["1", "OK", STEPS("A", "B")], ["2", "OK", STEPS("C")], ["3", "BAD", STEPS("D")]])
        self.inputs = os.path.join(d, "inputs.csv")
        write_csv(self.inputs, ["id", "text"], [["1", "x"], ["2", "y"], ["3", "z"]])
        self.template = os.path.join(d, "template.csv")
        write_csv(self.template, hdr, [])

    def tearDown(self):
        self.tmp.cleanup()

    def test_preflight_pass_and_fail(self):
        tool = script("hr-orchestrate-test-fix", "preflight.py")
        args = ["--template", self.template, "--inputs", self.inputs, "--id-col", "id",
                "--enum", "status=OK|BAD", "--json-col", "steps", "--all-required"]
        code, out = run(tool, self.exp, *args)
        self.assertEqual(code, 0, out)
        broken = os.path.join(self.d, "broken.csv")
        write_csv(broken, ["id", "status", "steps"], [["1", "MAYBE", "{bad"], ["1", "OK", "[]"]])
        code, out = run(tool, broken, *args)
        self.assertEqual(code, 1)
        for s in ("duplicated", "missing", "outside", "not valid JSON"):
            self.assertIn(s, out)

    def test_score_sample(self):
        code, out = run(script("hr-orchestrate-test-fix", "score_sample.py"), self.before, self.exp,
                        "--id-col", "id", "--json-col", "steps", "--json")
        self.assertEqual(code, 0, out)
        m = json.loads(out)
        self.assertEqual(m["columns"]["status"]["exact"], 2)
        self.assertEqual(m["columns"]["status"]["wrong_ids"], ["1"])
        self.assertEqual(m["columns"]["steps"]["steps"]["f1"], 1.0)

    def test_rerun_diff_verdicts(self):
        tool = script("hr-orchestrate-test-fix", "rerun_diff.py")
        code, out = run(tool, self.before, self.after, "--id-col", "id", "--expected", self.exp, "--json")
        self.assertEqual(json.loads(out)["verdict"], "KEEP")
        code, out = run(tool, self.after, self.worse, "--id-col", "id", "--expected", self.exp, "--json")
        r = json.loads(out)
        self.assertEqual(r["verdict"], "REVERT")
        self.assertEqual(sorted(r["broken"]), ["2", "3"])
        code, out = run(tool, self.after, self.after, "--id-col", "id", "--json")
        self.assertEqual(json.loads(out)["changed"], 0)

    def test_coupling_scan(self):
        code_dir = os.path.join(self.d, "code")
        os.makedirs(code_dir)
        open(os.path.join(code_dir, "rules.py"), "w").write('SPECIAL = "case_0042"\n')
        sample = os.path.join(self.d, "sample.csv")
        write_csv(sample, ["id", "text"], [["case_0042", "hello"]])
        code, out = run(script("hr-orchestrate-test-fix", "coupling_scan.py"), code_dir, "--sample", sample)
        self.assertEqual(code, 1)
        self.assertIn("case_0042", out)


class TestInterview(unittest.TestCase):
    def test_drill_and_coverage(self):
        with tempfile.TemporaryDirectory() as d:
            code_dir = os.path.join(d, "code")
            os.makedirs(code_dir)
            open(os.path.join(code_dir, "rules.py"), "w").write(
                'THRESHOLD = 0.75\nMODEL = "claude-haiku-5-5"\nRULE_ORDER = ["a", "b"]\n'
                'def f(x):\n    return x >= 45\n')
            consts = os.path.join(d, "CONSTANTS.md")
            open(consts, "w").write("| Name | Value |\n|---|---|\n| THRESHOLD | 0.75 |\n")
            tool = script("hr-orchestrate-interview", "interview_drill.py")
            code, out = run(tool, code_dir, "--no-general")
            self.assertEqual(code, 0, out)
            for s in ("THRESHOLD = 0.75", "claude-haiku-5-5", "RULE_ORDER", "45"):
                self.assertIn(s, out)
            code, out = run(tool, code_dir, "--constants", consts, "--strict", "--no-general")
            self.assertEqual(code, 1)
            self.assertIn("**MISSING**", out)
            self.assertIn("**COVERED**", out)


class TestPackage(unittest.TestCase):
    def test_package_build_and_secret_block(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "code", "data"))
            os.makedirs(os.path.join(d, "dataset"))
            os.makedirs(os.path.join(d, "evaluation"))
            os.makedirs(os.path.join(d, "tests"))
            open(os.path.join(d, "README.md"), "w").write("run: python code/main.py\n")
            open(os.path.join(d, "code", "main.py"), "w").write("print('hi')\n")
            open(os.path.join(d, "code", "data", "prompt.txt"), "w").write("prompt\n")
            open(os.path.join(d, "dataset", "big.csv"), "w").write("id\n1\n")
            open(os.path.join(d, ".env"), "w").write("ANTHROPIC_API_KEY=sk-ant-api03-abcdefghijklmnopqrstuvwxyz\n")
            open(os.path.join(d, ".env.example"), "w").write("ANTHROPIC_API_KEY=\n")
            open(os.path.join(d, "evaluation", "evaluation_report.md"), "w").write("report\n")
            open(os.path.join(d, "tests", "test_x.py"), "w").write("\n")
            open(os.path.join(d, "log.txt"), "w").write(GOOD_LOG)
            write_csv(os.path.join(d, "inputs.csv"), ["id", "t"], [["1", "a"], ["2", "b"]])
            write_csv(os.path.join(d, "template.csv"), ["id", "status"], [])
            write_csv(os.path.join(d, "output.csv"), ["id", "status"], [["1", "OK"], ["2", "BAD"]])
            tool = script("hr-orchestrate-package", "package.py")
            base = ["--root", d, "--template", os.path.join(d, "template.csv"), "--inputs",
                    os.path.join(d, "inputs.csv"), "--id-col", "id", "--require", "evaluation/evaluation_report.md",
                    "--exclude", "inputs.csv", "--exclude", "template.csv"]
            code, out = run(tool, *base)
            self.assertEqual(code, 0, out)
            with zipfile.ZipFile(os.path.join(d, "submission", "code.zip")) as z:
                names = set(z.namelist())
            self.assertIn("code/main.py", names)
            self.assertIn("code/data/prompt.txt", names)   # nested data dirs are kept
            self.assertIn(".env.example", names)
            self.assertNotIn(".env", names)
            self.assertFalse(any(n.startswith("dataset/") for n in names))
            self.assertNotIn("log.txt", names)
            self.assertTrue(os.path.isfile(os.path.join(d, "submission", "MANIFEST.md")))
            open(os.path.join(d, "code", "config.py"), "w").write('KEY = "sk-ant-api03-abcdefghijklmnopqrstuvwxyz"\n')
            code, out = run(tool, *base + ["--check-only"])
            self.assertEqual(code, 1)
            self.assertIn("possible secret in code/config.py", out)


if __name__ == "__main__":
    unittest.main()
