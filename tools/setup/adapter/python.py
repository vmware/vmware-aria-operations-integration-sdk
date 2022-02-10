import os

def build_template(path: str, root_directory: str):

    with open(os.path.join(path, root_directory, "collector.py"),'w') as collector:
        collector.write(
"""
import sys

def main(argv):
    if len(argv) == 0:
        print("No arguments")
    elif argv[0] in 'collect':
        print("Python collect")
    elif argv[0] in 'test':
        print("Python test")
    else:
        print(f"Command {argv[0]} not found")


if __name__ == '__main__':
    main(sys.argv[1:])

"""
        )
