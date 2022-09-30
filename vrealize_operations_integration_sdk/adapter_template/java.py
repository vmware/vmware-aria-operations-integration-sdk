#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

import os

def build_template(path: str, root_directory: str):
    with open(os.path.join(path, root_directory, "Collector.java"),'w') as collector:
        collector.write(
"""
public class Collector {
    public static void main(String[] args) {
        if (args.length == 0) {
            System.out.println("No Arguments");
        } else if (args[0].equals("collect")) {
            System.out.println("Java collect");
        } else if (args[0].equals("test")) {
            System.out.println("Java test");
        } else {
            System.out.println("Command "+ args[0] + " not found");
        }
    }
}

"""
        )

def compile(source_directory: str, output_directory: str):
    # compile class
    os.system(f"javac -d {output_directory} {source_directory}/Collector.java")
