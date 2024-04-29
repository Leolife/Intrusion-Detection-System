import process_checker


def main():

    print("\n--Process Checker--\n")

    process_list = "process_list"  # set this to the name of the txt file

    process = process_checker.ProcessChecker(process_list)

    process.check_running()


main()
