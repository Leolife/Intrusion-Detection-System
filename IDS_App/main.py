import os
import process_checker


def create_directory(dir_name, parent_dir_path):  # creates directory if one does not already exist
    directory = dir_name
    parent_dir = parent_dir_path
    path = os.path.join(parent_dir, directory)
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def create_file(output, dir_name, parent_dir_path):  # creates file for scan results
    folder_path = create_directory(dir_name, parent_dir_path)
    output_file = "output.txt"
    file_path = os.path.join(folder_path, output_file)
    i = 0
    while os.path.exists(file_path):  # in the case of duplicate output file names
        i += 1
        file_name, file_extension = os.path.splitext(output_file)
        output_file = f"{file_name}{i}{file_extension}"
        file_path = os.path.join(folder_path, output_file)
    with open(file_path, "w") as directory:
        directory.write(output)


def main():

    print("\n--Process Checker--\n")

    process_list = "process_list"  # set this to the name of the txt file

    process = process_checker.ProcessChecker(process_list)

    checker_result = process.check_running()

    dir_name = input("\nName of desired directory for scan results: ")

    parent_dir_path = input("\nParent directory path: ")

    create_file(checker_result, dir_name, parent_dir_path)

    print("\n--Process Check Complete--\n")


main()
