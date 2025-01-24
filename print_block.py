def print_block(string):
    frame = ""
    for _ in string:
        frame += "="
    print("\n")
    print(frame, flush=True)
    print(string, flush=True)
    print(frame, "\n", flush=True)


if __name__ == "__main__":
    print_block("This is a string")
