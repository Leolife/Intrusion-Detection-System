import process_checker


def add_to_file(output):  # currently functions as 'replace file' but finished product is 'add to file'
    with open("output.txt", "w") as output_file:
        output_file.write(output)


def main():

    print("\n--Process Checker--\n")

    process_list = "process_list"  # set this to the name of the txt file

    process = process_checker.ProcessChecker(process_list)

    checker_result = process.check_running()

    add_to_file(checker_result)

    print("\n--Process Check Complete--\n")


main()
