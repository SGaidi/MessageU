import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='MessageU',
        description='Run a MessageU server or client',
    )
    parser.add_argument(
        dest='run', choices=['server', 'client'],
    )
    parser.add_argument(
        dest='verbosity', action='store_true', help='enable debug logging',
    )
    args = parser.parse_args()

    if args.verbosity:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)

    if args.run == 'server':
        from serverapp import main
    else:  # args.run == 'client':
        from clientapp import main

    main.run()
