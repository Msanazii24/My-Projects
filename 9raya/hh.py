def calculate():
    print("Simple Calculator (type 'quit' to exit)")
    while True:
        expression = input("Enter expression (e.g. 2 + 3 * 4): ").strip()
        if expression.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break
        try:
            # eval is fine here because we only accept arithmetic characters
            cleaned = expression.replace("^", "**")
            if not all(ch in "0123456789+-*/(). %**" or ch.isspace() for ch in cleaned):
                raise ValueError("Unsupported characters detected.")
            result = eval(cleaned, {"__builtins__": {}}, {})
            print(f"Result: {result}")
        except Exception as exc:
            print(f"Error: {exc}")

if __name__ == "__main__":
    calculate()
