#!/usr/bin/env python3
import os


def main():
    print(os.environ.get("ADAPTER_KIND"))
    print(os.environ.get("ADAPTER_INSTANCE_OBJECT_KIND"))
    print(os.environ.get("SUITE_API_USER"))
    print(os.environ.get("SUITE_API_PASSWORD"))
    print(os.environ.get("CREDENTIAL_STRING"))


if __name__ == '__main__':
    main()

