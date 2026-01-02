#!/usr/bin/env python3
"""
Complexity Scorer for AI Coding Agents

Analyzes task descriptions and repository context to estimate complexity tier.
Provides recommendations for planning depth based on assessment.

Usage:
    python complexity_scorer.py "task description"
    python complexity_scorer.py --file plan.md
    python complexity_scorer.py --interactive
    python complexity_scorer.py "task" --path /path/to/repo --json
"""

import sys
import re
import os
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any

COMPLEXITY_INDICATORS = {
    "simple": {
        "keywords": [
            "rename", "fix", "update", "change", "add", "simple",
            "trivial", "minor", "small", "quick",
        ],
        "patterns": [
            r"^.{1,2}\s+files?",
            r"one\s+function",
            r"single\s+change",
            r"straightforward",
        ],
    },
    "moderate": {
        "keywords": [
            "feature", "implement", "create", "refactor", "function",
            "module", "endpoint", "integration", "component",
        ],
        "patterns": [
            r"\d+-\d+\s+files?",
            r"multiple\s+(files|functions|components)",
            r"new\s+(feature|module|api)",
            r"refactor.*module",
        ],
    },
    "complex": {
        "keywords": [
            "architecture", "system", "redesign", "migration",
            "platform", "infrastructure", "security", "performance",
            "scalability", "distributed", "microservice",
        ],
        "patterns": [
            r"\d+\+\s+files?",
            r"across\s+multiple",
            r"spans?\s+(the\s+)?(entire|whole|system)",
            r"architectural",
            r"breaking\s+change",
            r"major\s+refactor",
        ],
    },
}

RISK_MODIFIERS = {
    "high_risk": [
        "security", "authentication", "authorization", "payment",
        "production", "critical", "urgent", "breaking",
    ],
    "high_impact": [
        "user-facing", "customer", "revenue", "data", "migration",
        "legacy", "core", "infrastructure", "platform",
    ],
}

IGNORED_DIRS = {
    '.git', '.svn', '.hg', '.idea', '.vscode', '.venv', 'venv', 'env',
    'node_modules', 'dist', 'build', 'target', '__pycache__', 'coverage',
    '.next', '.nuxt', '.output', 'vendor'
}

@dataclass
class RepoStats:
    total_files: int
    total_dirs: int
    estimated_lines: int
    languages: Dict[str, int]
    is_large_repo: bool

@dataclass
class ComplexityResult:
    tier: str
    score: int
    confidence: str
    factors: List[str]
    recommendations: List[str]
    file_estimate: str
    time_estimate: str
    risk_level: str
    repo_stats: Optional[RepoStats] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def scan_repo(path: str) -> RepoStats:
    """Quickly scan repository to gather statistics."""
    root_path = Path(path)
    if not root_path.exists():
        return RepoStats(0, 0, 0, {}, False)

    total_files = 0
    total_dirs = 0
    estimated_lines = 0
    languages = {}
    
    # Simple extension mapping
    ext_map = {
        '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript', 
        '.jsx': 'React', '.tsx': 'React', '.java': 'Java', 
        '.c': 'C', '.cpp': 'C++', '.go': 'Go', '.rs': 'Rust',
        '.rb': 'Ruby', '.php': 'PHP', '.html': 'HTML', '.css': 'CSS',
        '.md': 'Markdown', '.json': 'JSON', '.yaml': 'YAML', '.yml': 'YAML'
    }

    try:
        for root, dirs, files in os.walk(path):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            total_dirs += len(dirs)
            
            for file in files:
                total_files += 1
                ext = Path(file).suffix.lower()
                if ext in ext_map:
                    lang = ext_map[ext]
                    languages[lang] = languages.get(lang, 0) + 1
                
                # Very rough line estimation based on file size
                # assuming avg 40 bytes per line for code
                try:
                    file_path = Path(root) / file
                    if not file_path.is_symlink():
                        size = file_path.stat().st_size
                        estimated_lines += size // 40
                except (OSError, ValueError):
                    pass

    except Exception:
        pass # Fail gracefully on permission errors etc.

    is_large = total_files > 1000 or estimated_lines > 50000

    return RepoStats(
        total_files=total_files,
        total_dirs=total_dirs,
        estimated_lines=estimated_lines,
        languages=languages,
        is_large_repo=is_large
    )


def analyze_text(text: str) -> Dict[str, int]:
    """Analyze text and return scores for each complexity level."""
    text_lower = text.lower()

    scores = {
        "simple": 0,
        "moderate": 0,
        "complex": 0,
        "epic": 0,
    }

    for level, indicators in COMPLEXITY_INDICATORS.items():
        for keyword in indicators["keywords"]:
            if keyword in text_lower:
                scores[level] += 1

        for pattern in indicators.get("patterns", []):
            if re.search(pattern, text_lower):
                scores[level] += 2

    if scores["complex"] >= 3 or scores["moderate"] >= 5:
        scores["epic"] = scores["complex"] + 2

    return scores


def analyze_file_count(text: str) -> Optional[str]:
    """Extract and analyze file count from text."""
    patterns = [
        r"(\d+)\s*files?",
        r"modify\s+(\d+)",
        r"update\s+(\d+)",
        r"(\d+)\s+modules?",
        r"(\d+)\s+components?",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            count = int(match.group(1))
            if count <= 2:
                return "simple"
            elif count <= 10:
                return "moderate"
            elif count <= 50:
                return "complex"
            else:
                return "epic"

    return None


def calculate_risk_level(text: str) -> str:
    """Calculate risk level based on content."""
    text_lower = text.lower()
    risk_score = 0

    for keyword in RISK_MODIFIERS["high_risk"]:
        if keyword in text_lower:
            risk_score += 1

    for keyword in RISK_MODIFIERS["high_impact"]:
        if keyword in text_lower:
            risk_score += 1

    if risk_score >= 3:
        return "High"
    elif risk_score >= 1:
        return "Medium"
    else:
        return "Low"


def estimate_files(text: str) -> str:
    """Estimate number of files affected."""
    text_lower = text.lower()

    file_indicators = {
        "1-2": ["single", "one file", "one function", "rename", "simple fix"],
        "3-10": ["feature", "multiple files", "3-", "5-", "new function"],
        "10-50": ["refactor", "module", "component", "10 files", "15 files"],
        "50+": ["system", "platform", "architecture", "migration", "entire"],
    }

    for count_range, indicators in file_indicators.items():
        for indicator in indicators:
            if indicator in text_lower:
                return count_range

    return "Unknown"


def estimate_time(text: str) -> str:
    """Estimate time required."""
    text_lower = text.lower()

    time_indicators = {
        "30min-2hr": ["quick", "simple", "minor", "small change"],
        "4hr-1day": ["straightforward", "routine", "standard"],
        "1-3days": ["feature", "implementation", "moderate"],
        "1-2weeks": ["complex", "significant", "major"],
        "1+month": ["system-wide", "platform", "migration", "epic"],
    }

    for time_range, indicators in time_indicators.items():
        for indicator in indicators:
            if indicator in text_lower:
                return time_range

    score_result = analyze_text(text)
    max_score = max(score_result.values())

    if max_score <= 1:
        return "30min-2hr"
    elif max_score <= 3:
        return "4hr-1day"
    elif score_result.get("complex", 0) >= 2:
        return "1-2weeks"
    else:
        return "1-3days"


def determine_tier(text: str, repo_stats: Optional[RepoStats] = None) -> ComplexityResult:
    """Determine the complexity tier for a task."""
    text_lower = text.lower()

    scores = analyze_text(text)
    file_estimate = analyze_file_count(text)

    if not file_estimate:
        file_estimate = estimate_files(text)

    time_estimate = estimate_time(text)
    risk_level = calculate_risk_level(text)

    # Adjust scores based on repo stats
    factors = []
    
    if repo_stats and repo_stats.is_large_repo:
        # In a large repo, "refactors" and "migrations" are inherently riskier/harder
        if "refactor" in text_lower or "move" in text_lower:
            scores["complex"] += 1
            scores["moderate"] += 1
            factors.append("Large repo detected: Refactoring complexity increased")
        if "test" in text_lower or "coverage" in text_lower:
            scores["moderate"] += 1
            factors.append("Large repo detected: Testing scope potentially larger")

    if not file_estimate:
        max_score = max(scores.values())
        if scores["simple"] == max_score and max_score >= 2:
            file_estimate = "1-2"
        elif scores["moderate"] == max_score and max_score >= 3:
            file_estimate = "3-10"
        elif scores["complex"] == max_score and max_score >= 2:
            file_estimate = "10-50"
        else:
            file_estimate = "Unknown"

    if scores["epic"] >= 4:
        tier = "Epic"
        score = 4
    elif scores["complex"] >= 3 or file_estimate in ["50+", "10-50"]:
        tier = "Complex"
        score = 3
    elif scores["moderate"] >= 3 or file_estimate in ["3-10"]:
        tier = "Moderate"
        score = 2
    else:
        tier = "Simple"
        score = 1

    # Override for large repos if unsure
    if repo_stats and repo_stats.is_large_repo and tier == "Simple" and "fix" not in text_lower:
         # Unless it's explicitly a "fix" or "simple", bias towards Moderate in large repos
         if scores["moderate"] >= 1:
             tier = "Moderate"
             score = 2
             factors.append("Large repo bias: Upgraded from Simple to Moderate")

    if scores["simple"] >= 2:
        factors.append("Simple task indicators present")
    if scores["moderate"] >= 3:
        factors.append("Moderate complexity indicators")
    if scores["complex"] >= 2:
        factors.append("Complex task indicators")
    if scores["epic"] >= 2:
        factors.append("Epic-scale indicators")
    if risk_level in ["High", "Medium"]:
        factors.append(f"Risk level: {risk_level}")

    confidence = "High" if max(scores.values()) >= 3 else "Medium" if max(scores.values()) >= 1 else "Low"

    recommendations = []
    if tier == "Simple":
        recommendations = [
            "Brief planning phase (5-10 minutes)",
            "Focus on: Understanding + Breakdown + Verification",
            "Skip detailed architecture",
        ]
    elif tier == "Moderate":
        recommendations = [
            "Full 7-phase planning",
            "Include option analysis",
            "Document dependencies and risks",
        ]
    elif tier == "Complex":
        recommendations = [
            "Detailed architecture review",
            "Comprehensive risk assessment",
            "Staged implementation approach",
            "Consider peer review of plan",
        ]
    elif tier == "Epic":
        recommendations = [
            "Requires architectural review",
            "Phase the implementation",
            "Create ADRs (Architecture Decision Records)",
            "Multi-stakeholder alignment needed",
        ]

    return ComplexityResult(
        tier=tier,
        score=score,
        confidence=confidence,
        factors=factors,
        recommendations=recommendations,
        file_estimate=file_estimate,
        time_estimate=time_estimate,
        risk_level=risk_level,
        repo_stats=repo_stats
    )


def print_result_text(result: ComplexityResult, task_description: str) -> None:
    """Print complexity assessment result in text format."""
    print("Complexity Assessment")
    print("=" * 50)
    print(f"Task: {task_description[:60]}...")
    print()
    print(f"Tier: {result.tier}")
    print(f"Files: ~{result.file_estimate}")
    print(f"Time: {result.time_estimate}")
    print(f"Risk: {result.risk_level}")
    print(f"Confidence: {result.confidence}")
    
    if result.repo_stats:
        print()
        print(f"Repository Context:")
        print(f"  Files: {result.repo_stats.total_files}")
        print(f"  Languages: {', '.join(k for k,v in sorted(result.repo_stats.languages.items(), key=lambda item: item[1], reverse=True)[:3])}")
        if result.repo_stats.is_large_repo:
            print(f"  Status: LARGE REPOSITORY")

    print()

    if result.factors:
        print("Factors:")
        for factor in result.factors:
            print(f"  - {factor}")
        print()

    print("Recommendations:")
    for rec in result.recommendations:
        print(f"  - {rec}")
    print()


def analyze_file(path: str, repo_path: Optional[str] = None) -> ComplexityResult:
    """Analyze a plan file."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    content = file_path.read_text()
    repo_stats = scan_repo(repo_path) if repo_path else None
    return determine_tier(content, repo_stats)


def interactive_mode(repo_path: Optional[str] = None) -> None:
    """Run in interactive mode."""
    print("Complexity Scorer - Interactive Mode")
    print("=" * 50)
    repo_stats = scan_repo(repo_path) if repo_path else None
    
    if repo_stats:
        print(f"Context: {repo_stats.total_files} files in {repo_path}")
        
    print("Enter task description (or 'quit' to exit):")
    print()

    while True:
        try:
            task = input("> ").strip()
        except EOFError:
            break

        if not task:
            continue

        if task.lower() in ["quit", "exit", "q"]:
            break

        result = determine_tier(task, repo_stats)
        print()
        print_result_text(result, task)
        print()


def main():
    parser = argparse.ArgumentParser(description="AI Agent Complexity Scorer")
    parser.add_argument("input", nargs="*", help="Task description or input text")
    parser.add_argument("--file", "-f", help="Path to a plan file to analyze")
    parser.add_argument("--path", "-p", help="Path to repository to scan for context", default=".")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    parser.add_argument("--json", "-j", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    # Determine mode
    if args.interactive:
        interactive_mode(args.path)
        return 0

    repo_stats = scan_repo(args.path)
    
    result = None
    task_desc = ""

    if args.file:
        try:
            result = analyze_file(args.file, args.path)
            task_desc = Path(args.file).name
        except Exception as e:
            if args.json:
                print(json.dumps({"error": str(e)}))
            else:
                print(f"Error: {e}")
            return 1
    elif args.input:
        task_desc = " ".join(args.input)
        result = determine_tier(task_desc, repo_stats)
    else:
        # No input provided, default to interactive
        if not args.json:
            interactive_mode(args.path)
            return 0
        else:
            print(json.dumps({"error": "No input provided"}))
            return 1

    if args.json:
        # Enrich dict with task description for context
        res_dict = result.to_dict()
        res_dict["task_description"] = task_desc
        print(json.dumps(res_dict, indent=2))
    else:
        print_result_text(result, task_desc)

    return 0


if __name__ == "__main__":
    sys.exit(main())