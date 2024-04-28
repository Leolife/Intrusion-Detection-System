import process_checker


def main():

    print("Process Checker\n")
    process_to_check = input("What process would you like to check for? ")
    process = process_checker.ProcessChecker(process_to_check)
    process.check_running()



main()