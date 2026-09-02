from context import build_context


def get_ai_context(query: str) -> str:
    """
    Build optimized code context for any AI provider.

    The AI provider is intentionally not specified here.
    """

    return build_context(query)


if __name__ == "__main__":

    import sys

    if len(sys.argv) < 2:
        print(
            'Usage: python ai_graph/ai_context.py '
            '"your problem"'
        )
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    context = get_ai_context(query)

    print(context)
