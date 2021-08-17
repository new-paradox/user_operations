import user_operation
import argparse


if __name__ == '__main__':
    manager = argparse.ArgumentParser(description='Users operation')
    manager.add_argument('-S', '--src', type=str, metavar='', help='input file')
    manager.add_argument('-C', '--count', type=int, metavar='', help='count of operation')

    args = manager.parse_args()
    parser = user_operation.Controller(json_file=args.src, count_row=args.count)
    print(parser)
