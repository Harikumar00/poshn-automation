import ast
from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]

EXCLUDED_DIRS = {
    ".venv",
    "__pycache__",
    ".git",
    "reports",
    "test-results",
}


def python_files():
    return [
        path
        for path in ROOT.rglob("*.py")
        if not any(part in EXCLUDED_DIRS for part in path.parts)
    ]


def module_name(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("/", ".").removesuffix(".py")


def analyze_file(path: Path):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imports = []
    classes = []
    functions = []

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):
            for item in node.names:
                imports.append(item.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)

    return {
        "file": str(path.relative_to(ROOT)),
        "module": module_name(path),
        "imports": sorted(set(imports)),
        "classes": sorted(set(classes)),
        "functions": sorted(set(functions)),
    }


def build_graph():
    graph = []

    for path in python_files():
        try:
            graph.append(analyze_file(path))
        except Exception as exc:
            print(f"Skipping {path}: {exc}")

    return graph


if __name__ == "__main__":
    output = ROOT / "ai_graph" / "code_graph.json"

    graph = build_graph()

    output.write_text(
        json.dumps(graph, indent=2),
        encoding="utf-8",
    )

    print(f"Indexed {len(graph)} Python files")
    print(f"Graph written to: {output}")
