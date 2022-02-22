import os
import zipfile


def get_absolute_project_directory(*path: [str]):
    return os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "", "../..", *path))


def mkdir(basepath, *paths):
    path = os.path.join(basepath, *paths)
    if not os.path.exists(path):
        os.mkdir(path, 0o755)
    return path


def zip_dir(zip_file, directory):
    for file in files_in_directory(directory):
        zip_file.write(file, compress_type=zipfile.ZIP_DEFLATED)


def files_in_directory(directory):
    result = []
    for root, directories, files in os.walk(directory):
        print(f"Root: {root}")
        print(f"Directories: {directories}")
        print(f"Files: {files}")

        for filename in files:
            result.append(os.path.join(root, filename))
        for subdirectory in directories:
            for filename in files_in_directory(subdirectory):
                result.append(os.path.join(root, filename))
    return result
