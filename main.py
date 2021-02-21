import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="messageu",
        description="Run a messageu server or client",
    )
    parser.add_argument(
        dest="run", choices=["server", "client"],
    )
    args = parser.parse_args()

    if args.run == "server":
        from serverapp import main
    else:  # args.run == "client":
        from clientapp import main

    main.run()
