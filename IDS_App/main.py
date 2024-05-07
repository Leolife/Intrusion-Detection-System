import os
import process_checker
import port_scan


def create_directory(dir_name, parent_dir_path):  # creates directory if one does not already exist
    directory = dir_name
    parent_dir = parent_dir_path
    path = os.path.join(parent_dir, directory)
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def create_file(output, dir_name, parent_dir_path, output_file):  # creates file for scan results
    folder_path = create_directory(dir_name, parent_dir_path)
    output_file += ".txt"
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

    dir_name = input("Name of desired directory for results: ")
    parent_dir_path = input("Parent directory path: ")
    try:
        option = (input("\nChoose an option:\n   1) Check for specific processes\n   2) Port Scan\n   3) All\n >>"))
        if option == 1:
            results = ""
            print("\n--Process Checker--\n")
            file_name = input("Output file name: ")
            process_list = "process_list"  # set this to the name of the txt file
            process = process_checker.ProcessChecker(process_list)
            results += process.check_running()
            create_file(results, dir_name, parent_dir_path, file_name)
            print("\n--Process Check Complete--\n")
        elif option == 2:
            results = ""
            print("\n--Port Scan--\n")
            file_name = input("Output file name: ")
            scan = port_scan.PortScan()
            results += scan.search_for_packets()
            create_file(results, dir_name, parent_dir_path, file_name)
            print("\n--Port Scan Complete--\n")
        elif option == 3:
            results = ""
            file_name = input("Output file name: ")
            print("\n--Process Checker--\n")
            process_list = "process_list"  # set this to the name of the txt file
            process = process_checker.ProcessChecker(process_list)
            results += process.check_running()
            print("\n--Process Check Complete--\n")
            print("\n--Port Scan--\n")
            scan = port_scan.PortScan()
            results += scan.search_for_packets()
            create_file(results, dir_name, parent_dir_path, file_name)
            print("\n--Port Scan Complete--\n")
        else:
            raise TypeError
    except TypeError:
        print("Choose a valid integer corresponding to the number of desired option.")


main()
