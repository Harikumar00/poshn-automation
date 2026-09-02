import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GRAPH_FILE = ROOT / "ai_graph" / "code_graph.json"


STOP_WORDS = {
    "the", "is", "a", "an", "and", "or", "to", "of",
    "in", "on", "for", "with", "from", "this", "that",
    "test", "tests", "failing", "failed", "error",
    "issue", "please", "fix",
}


def load_graph():
    return json.loads(
        GRAPH_FILE.read_text(encoding="utf-8")
    )


def tokenize(text):
    words = re.findall(
        r"[a-zA-Z_][a-zA-Z0-9_]*",
        text.lower(),
    )

    tokens = set()

    for word in words:

        if word in STOP_WORDS:
            continue

        tokens.add(word)

        parts = word.split("_")

        for part in parts:
            if len(part) > 2 and part not in STOP_WORDS:
                tokens.add(part)

    return tokens


def node_tokens(node):
    tokens = set()

    tokens.update(
        tokenize(node["file"])
    )

    tokens.update(
        tokenize(node["module"])
    )

    for item in node.get("imports", []):
        tokens.update(
            tokenize(item)
        )

    for cls in node.get("classes", []):

        tokens.update(
            tokenize(cls["name"])
        )

        for method in cls.get("methods", []):
            tokens.update(
                tokenize(method["name"])
            )

    for function in node.get("functions", []):
        tokens.update(
            tokenize(function["name"])
        )

    return tokens


def base_score(node, query_tokens):
    score = 0
    reasons = []

    file = node["file"].lower()
    file_tokens = tokenize(file)

    # File / module match
    file_matches = query_tokens & file_tokens

    if file_matches:
        score += 6 * len(file_matches)

        for token in file_matches:
            reasons.append(
                f"filename:{token}"
            )

    # Class match
    for cls in node.get("classes", []):

        class_tokens = tokenize(
            cls["name"]
        )

        matched = query_tokens & class_tokens

        if matched:
            score += 20 * len(matched)

            reasons.append(
                f"class:{cls['name']}"
            )

    # Method match
    for cls in node.get("classes", []):

        for method in cls.get("methods", []):

            method_tokens = tokenize(
                method["name"]
            )

            matched = query_tokens & method_tokens

            if not matched:
                continue

            score += 25 * len(matched)

            reasons.append(
                f"method:{cls['name']}.{method['name']}"
            )

    # Standalone function match
    for function in node.get("functions", []):

        function_tokens = tokenize(
            function["name"]
        )

        matched = query_tokens & function_tokens

        if not matched:
            continue

        score += 8 * len(matched)

        reasons.append(
            f"function:{function['name']}"
        )

    # Import match
    for imported in node.get("imports", []):

        imported_tokens = tokenize(
            imported
        )

        matched = query_tokens & imported_tokens

        if matched:

            score += 2 * len(matched)

            for token in matched:
                reasons.append(
                    f"import:{token}"
                )

    # Project structure
    if file.startswith("tests/"):
        score += 2

    elif file.startswith("pages/"):
        score += 3

    elif file.startswith("components/"):
        score += 1

    return score, list(
        dict.fromkeys(reasons)
    )


def build_relationships(graph):

    relationships = {}

    for node in graph:

        relationships[node["module"]] = set(
            node.get("imports", [])
        )

    return relationships


def dependency_bonus(
    node,
    ranked_modules,
    relationships,
):
    score = 0
    reasons = []

    module = node["module"]

    for source_module, imports in relationships.items():

        if source_module not in ranked_modules:
            continue

        if module in imports:

            score += 6

            reasons.append(
                f"dependency-of:{source_module}"
            )

    return score, reasons


def search(query, limit=3):

    graph = load_graph()

    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    relationships = build_relationships(
        graph
    )

    nodes_by_module = {
        node["module"]: node
        for node in graph
    }

    # 1. Score every file
    initial = []

    for node in graph:

        score, reasons = base_score(
            node,
            query_tokens,
        )

        if score > 0:

            initial.append({
                "node": node,
                "score": score,
                "reasons": reasons,
            })

    initial.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    # 2. Strong matches become graph anchors
    anchor_modules = {
        item["node"]["module"]
        for item in initial[:3]
    }

    # 3. Add dependency relationships
    results = []

    for item in initial:

        node = item["node"]

        bonus, bonus_reasons = dependency_bonus(
            node,
            anchor_modules,
            relationships,
        )

        results.append({
            "score": item["score"] + bonus,
            "file": node["file"],
            "reasons": (
                item["reasons"]
                + bonus_reasons
            ),
        })

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    # Only return genuinely relevant files
    results = [
        result
        for result in results
        if result["score"] >= 8
    ]

    return results[:limit]


def main():

    if len(sys.argv) < 2:

        print(
            'Usage: python ai_graph/search.py '
            '"your problem"'
        )

        sys.exit(1)

    query = " ".join(
        sys.argv[1:]
    )

    print()
    print("=" * 60)
    print("POSN CODE GRAPH SEARCH")
    print("=" * 60)
    print(f"Query: {query}")
    print()

    results = search(query)

    if not results:

        print(
            "No relevant files found."
        )

        return

    for index, result in enumerate(
        results,
        start=1,
    ):

        print(
            f"{index}. {result['file']} "
            f"(score={result['score']})"
        )

        if result["reasons"]:

            print(
                "   "
                + " | ".join(
                    result["reasons"][:8]
                )
            )

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
