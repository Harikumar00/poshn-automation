import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXCLUDED_DIRS = {
    ".venv",
    "__pycache__",
    ".git",
    "reports",
    "test-results",
    "ai_graph",
}


def python_files():
    return [
        path
        for path in ROOT.rglob("*.py")
        if path.name != "__init__.py"
        and not any(part in EXCLUDED_DIRS for part in path.parts)
    ]


def module_name(path: Path) -> str:
    return (
        str(path.relative_to(ROOT))
        .replace("/", ".")
        .removesuffix(".py")
    )


def get_name(node):
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        return node.attr

    return None


def get_methods(class_node):
    methods = []

    for node in class_node.body:

        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            methods.append({
                "name": node.name,
                "async": isinstance(
                    node,
                    ast.AsyncFunctionDef,
                ),
            })

    return methods


def analyze_file(path: Path):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imports = []
    classes = []
    functions = []
    calls = []
    inheritance = []

    for node in ast.walk(tree):

        # import x
        if isinstance(node, ast.Import):

            for item in node.names:
                imports.append(item.name)

        # from x import y
        elif isinstance(node, ast.ImportFrom):

            if node.module:
                imports.append(node.module)

        # class X(...)
        elif isinstance(node, ast.ClassDef):

            bases = []

            for base in node.bases:

                name = get_name(base)

                if name:
                    bases.append(name)

                    inheritance.append({
                        "class": node.name,
                        "inherits": name,
                    })

            classes.append({
                "name": node.name,
                "bases": bases,
                "methods": get_methods(node),
            })

        # def x(...)
        elif isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):

            functions.append({
                "name": node.name,
                "async": isinstance(
                    node,
                    ast.AsyncFunctionDef,
                ),
            })

        # function/method calls
        elif isinstance(node, ast.Call):

            name = get_name(node.func)

            if name:
                calls.append(name)

    return {
        "file": str(path.relative_to(ROOT)),
        "module": module_name(path),
        "imports": sorted(set(imports)),
        "classes": classes,
        "functions": functions,
        "calls": sorted(set(calls)),
        "inheritance": inheritance,
    }


def build_graph():
    graph = []

    for path in python_files():

        try:
            graph.append(
                analyze_file(path)
            )

        except Exception as exc:

            print(
                f"Skipping {path}: {exc}"
            )

    return graph


def main():

    output = (
        ROOT
        / "ai_graph"
        / "code_graph.json"
    )

    graph = build_graph()

    output.write_text(
        json.dumps(
            graph,
            indent=2,
        ),
        encoding="utf-8",
    )

    total_classes = sum(
        len(node["classes"])
        for node in graph
    )

    total_methods = sum(
        len(cls["methods"])
        for node in graph
        for cls in node["classes"]
    )

    total_functions = sum(
        len(node["functions"])
        for node in graph
    )

    print()
    print("=" * 60)
    print("POSN CODE GRAPH")
    print("=" * 60)
    print(f"Python files indexed : {len(graph)}")
    print(f"Classes indexed      : {total_classes}")
    print(f"Methods indexed      : {total_methods}")
    print(f"Functions indexed    : {total_functions}")
    print(f"Graph file           : {output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
