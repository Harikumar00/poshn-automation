import ast
import sys
from pathlib import Path

from search import search


ROOT = Path(__file__).resolve().parents[1]


def read_source(file_path):
    path = ROOT / file_path
    return path.read_text(encoding="utf-8")


def tokenize(text):
    words = text.lower().replace("_", " ").split()

    return {
        word
        for word in words
        if len(word) > 2
    }


def extract_relevant_code(source, query):
    tree = ast.parse(source)
    query_tokens = tokenize(query)

    results = []

    for node in tree.body:

        if isinstance(node, ast.ClassDef):

            class_tokens = tokenize(node.name)
            class_match = query_tokens & class_tokens

            for child in node.body:

                if not isinstance(
                    child,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                    ),
                ):
                    continue

                method_tokens = tokenize(child.name)
                matched = query_tokens & method_tokens

                if matched:

                    code = ast.get_source_segment(
                        source,
                        child,
                    )

                    if code:
                        results.append({
                            "type": "method",
                            "name": f"{node.name}.{child.name}",
                            "score": 30 * len(matched),
                            "code": code,
                        })

            # Only include the whole class when the class name
            # itself is the relevant match and no method matched.
            if class_match and not any(
                item["type"] == "method"
                for item in results
            ):

                code = ast.get_source_segment(
                    source,
                    node,
                )

                if code:
                    results.append({
                        "type": "class",
                        "name": node.name,
                        "score": 20 * len(class_match),
                        "code": code,
                    })

        elif isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):

            function_tokens = tokenize(node.name)
            matched = query_tokens & function_tokens

            if matched:

                code = ast.get_source_segment(
                    source,
                    node,
                )

                if code:
                    results.append({
                        "type": "function",
                        "name": node.name,
                        "score": 15 * len(matched),
                        "code": code,
                    })

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return results


def build_context(query, max_files=3):

    results = search(
        query,
        limit=max_files,
    )

    context_parts = []

    for result in results:

        file_path = result["file"]

        try:

            source = read_source(file_path)

            definitions = extract_relevant_code(
                source,
                query,
            )

            # Skip files where the graph only found a weak
            # dependency relationship and no relevant definition.
            if not definitions:
                continue

            context_parts.append(
                f"FILE: {file_path}\n"
            )

            for definition in definitions[:4]:

                context_parts.append(
                    f"\n"
                    f"{definition['type'].upper()}: "
                    f"{definition['name']}\n"
                )

                context_parts.append(
                    definition["code"]
                )

                context_parts.append("\n")

        except Exception as exc:

            context_parts.append(
                f"\n"
                f"ERROR READING {file_path}: "
                f"{exc}\n"
            )

    return "\n".join(context_parts)


def main():

    if len(sys.argv) < 2:

        print(
            'Usage: python ai_graph/context.py '
            '"your problem"'
        )

        sys.exit(1)

    query = " ".join(sys.argv[1:])

    print()
    print("=" * 70)
    print("POSN AI CONTEXT")
    print("=" * 70)
    print()

    context = build_context(query)

    print(context)

    print()
    print("=" * 70)
    print(
        f"Context characters: "
        f"{len(context):,}"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
