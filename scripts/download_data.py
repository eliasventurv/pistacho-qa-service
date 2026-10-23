from datasets import load_dataset


def main():
    ds = load_dataset("squad_v2")
    print(ds)


if __name__ == "__main__":
    main()
