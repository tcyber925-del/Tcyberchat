#!/usr/bin/env python3
"""
Plan Validator for AI Coding Agents

Validates implementation plans for completeness and quality.
Checks for missing sections, logical issues, and common problems.

Usage:
    python plan_validator.py <plan_file.md>
    python plan_validator.py --interactive
    python plan_validator.py <plan_file.md> --json
"""

import sys
import re
import json
import argparse
from pathlib import Path
from typing import List, Tuple, Dict, Any

SECTIONS = [
    "understanding",
    "analysis",
    "architecture",
    "breakdown",
    "dependencies",
    "risk",
    "verification",
]

SECTION_PATTERNS = {
    "understanding": r"(?i)^#+\s*(1\.\s*)?(understanding|clarification|overview)",
    "analysis": r"(?i)^#+\s*(2\.\s*)?(analysis|context|gathering)",
    "architecture": r"(?i)^#+\s*(3\.\s*)?(architecture|design|approach|technical)",
    "breakdown": r"(?i)^#+\s*(4\.\s*)?(breakdown|tasks?|implementation)",
    "dependencies": r"(?i)^#+\s*(5\.\s*)?(dependencies?|prerequisites)",
    "risk": r"(?i)^#+\s*(6\.\s*)?(risk|challenges|mitigation)",
    "verification": r"(?i)^#+\s*(7\.\s*)?(verification|testing|validation)",
}

def get_section_content(plan_content: str, section_name: str) -> str:
    """Extract content for a specific section."""
    lines = plan_content.split("\n")

    section_start = -1
    for i, line in enumerate(lines):
        if re.search(SECTION_PATTERNS.get(section_name, ""), line):
            section_start = i
            break

    if section_start == -1:
        return ""

    section_end = len(lines)
    for i in range(section_start + 1, len(lines)):
        # Stop at next header of same or higher level, assuming standard markdown
        if re.match(r"^#+\s", lines[i]): 
             # Basic check: if it matches another known section or just any header
             # Ideally we check level, but for now assuming flat structure
             section_end = i
             break

    return "\n".join(lines[section_start+1:section_end]).strip()


def validate_plan(plan_content: str) -> Tuple[bool, List[str], List[str]]:
    """Validate a plan and return (is_valid, critical_issues, warnings)."""
    issues = []
    warnings = []
    lines = plan_content.split("\n")

    # 1. Structural Checks
    section_positions = {}
    for i, line in enumerate(lines):
        for section, pattern in SECTION_PATTERNS.items():
            if re.search(pattern, line):
                section_positions[section] = i
                break

    missing_sections = set(SECTIONS) - set(section_positions.keys())
    for section in missing_sections:
        issues.append(f"Missing section: {section.title()}")

    section_order = list(section_positions.items())
    section_order.sort(key=lambda x: x[1])

    prev_pos = -1
    for section, pos in section_order:
        if pos < prev_pos:
            warnings.append(f"Section order issue: {section.title()} appears out of order")
        prev_pos = pos

    # 2. Content Checks
    task_pattern = r"(?i)^[-*]\s*task[:\s]"
    task_count = sum(1 for line in lines if re.search(task_pattern, line))
    
    is_complex = "complex" in plan_content.lower() or "epic" in plan_content.lower()
    
    if task_count == 0:
        if is_complex:
             issues.append("Complex/Epic plan requires explicit Task Breakdown (e.g. 'Task: ...')")
        else:
             warnings.append("No explicit tasks found (look for lines starting with '- Task:')")

    # Risk Check
    risk_content = get_section_content(plan_content, "risk")
    if is_complex and len(risk_content) < 20:
        issues.append("Complex plan must have a detailed Risk Assessment")
    
    # Verification Check
    verify_content = get_section_content(plan_content, "verification")
    if not verify_content:
        issues.append("Verification section is empty")
    else:
        # Check for actionable content (code blocks or shell commands)
        if "```" not in verify_content and "`" not in verify_content and "npm" not in verify_content and "python" not in verify_content:
             warnings.append("Verification section lacks actionable commands or code blocks")

    # 3. Depth Checks
    for section in SECTIONS:
        content = get_section_content(plan_content, section)
        if section in section_positions and len(content.split()) < 5:
             warnings.append(f"Section '{section.title()}' seems very short (< 5 words).")

    return len(issues) == 0, issues, warnings


def validate_file(path: str, as_json: bool = False) -> int:
    """Validate a plan file and return exit code."""
    file_path = Path(path)

    if not file_path.exists():
        err = f"Error: File not found: {path}"
        if as_json:
            print(json.dumps({"valid": False, "errors": [err]}))
        else:
            print(err)
        return 1

    try:
        content = file_path.read_text()
    except Exception as e:
        err = f"Error reading file: {e}"
        if as_json:
            print(json.dumps({"valid": False, "errors": [err]}))
        else:
            print(err)
        return 1

    is_valid, issues, warnings = validate_plan(content)

    if as_json:
        result = {
            "valid": is_valid,
            "file": str(file_path),
            "errors": issues,
            "warnings": warnings,
            "status": "PASS" if is_valid else "FAIL"
        }
        print(json.dumps(result, indent=2))
        return 0 if is_valid else 1

    print(f"Validating: {file_path.name}")
    print("=" * 50)

    print(f"Status: {'VALID' if is_valid else 'ISSUES FOUND'}")
    print()

    if issues:
        print("CRITICAL ISSUES:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        print()

    if warnings:
        print("SUGGESTIONS/WARNINGS:")
        for i, issue in enumerate(warnings, 1):
            print(f"  {i}. {issue}")
        print()

    if not is_valid:
        print("FAIL: Plan has structural issues that should be addressed")
        return 1
    elif warnings:
        print("PASS with suggestions: Plan is valid but could be improved")
        return 0
    else:
        print("PASS: Plan is complete and well-structured")
        return 0


def interactive_mode(as_json: bool = False) -> None:
    """Interactive plan validation."""
    if not as_json:
        print("Plan Validator - Interactive Mode")
        print("=" * 50)
        print("Paste your plan below (Ctrl+D or Ctrl+Z to finish):")
        print()

    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass

    content = "\n".join(lines)
    is_valid, issues, warnings = validate_plan(content)

    if as_json:
        result = {
            "valid": is_valid,
            "errors": issues,
            "warnings": warnings
        }
        print(json.dumps(result, indent=2))
    else:
        print()
        print("Validating...")
        print()
        print(f"Status: {'VALID' if is_valid else 'ISSUES FOUND'}")
        
        if issues:
            print("Issues:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
        if warnings:
            print("Warnings:")
            for i, warn in enumerate(warnings, 1):
                print(f"  {i}. {warn}")
        
        if not issues and not warnings:
             print("No issues found.")

def main():
    parser = argparse.ArgumentParser(description="AI Agent Plan Validator")
    parser.add_argument("file", nargs="?", help="Plan file to validate")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    parser.add_argument("--json", "-j", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    if args.interactive or not args.file:
        interactive_mode(args.json)
        return 0

    return validate_file(args.file, args.json)


if __name__ == "__main__":
    sys.exit(main())