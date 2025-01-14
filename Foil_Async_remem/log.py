import glovars
import ntptime
import time
import os
import comm


def file_or_dir_exists(filename):
    r = False
    try:
        os.stat(filename)
    except OSError:
        r = False
    else:
        r = True
    finally:
        return r


def log_err(code, call_function=None, e=None):
    """
    Logs an error with the given code, mode, and optional details.
    Prompt uploads it to NC server

    Parameters:
        code (str): The error code.
        mode (str): The mode of logging ("file", "mem", or "both").
        call_function (str): The name of the calling function (optional).
        e (str): Additional error details (optional).
    """
    # Cut the post string to max 64 char length
    call_function = call_function or "UnknownFunction"  # Default if None
    e = e or "NoDetails"  # Default if None
    cut_data = f"{code}-{call_function}-{e}"[:64]

    try:
        # Extract integer code from `code`, assuming format like "Err123"
        code_int = int(code[3:]) if len(code) > 3 and code[:3].isalpha() else 0
    except ValueError:
        code_int = 0

    # Log to file
    log_to_file("error_log.txt", cut_data, ntptime.time_format("sec"),
                code_int)
    # Build log
    build_one_log(cut_data, ntptime.time_format("sec"), code_int)

    # Upload log prompt
    try:
        comm.upload_data("err")
    except Exception as e:
        print(f"Error uploading error log: {e}")


#This funtion uses the general pre-allocated dict "upload_one" and filles up with parameters received
def build_one_log(dimension1, dimension2, value):
    glovars.upload_one["data"][0]["dimension1"] = dimension1
    glovars.upload_one["data"][0]["dimension2"] = dimension2
    glovars.upload_one["data"][0]["value"] = value


def log_sys(logstr):
    build_one_log(logstr[:64], ntptime.time_format("sec"), 0)
    # Upload log prompt
    try:
        comm.upload_data("sys")
    except Exception as e:
        print(f"Error uploading system log: {e}")
        log_err("Err4", "log_sys", e)


def log_to_file(filename, dataname1, dataname2, datavalue):
    # Check if the file exists, if not, create it
    mod = 'a' if file_or_dir_exists(filename) else 'w'
    try:
        with open(filename, mod) as file:
            file.write(f"{dataname1}, {dataname2}, {datavalue}\n")
    except OSError as e:
        print(f"Error writing to file {filename}: {e}")


def log_dict_file(filename,costtype,cost,timestamp=None):
    '''this function puts mid-frequently logged data to a flatfile for minimize heap usage
   
    principles:
    Dict-like structure:
    1. the data is stored in a dict, with the key being the costtype
    2. the dict is stored in a list, with the key being the timestamp
    3. the dict is stored in a flatfile, with the key being the timestamp
    Uptate or append if not existing
    Input:
    electricity,2025-01-09,50
    water,2025-01-09,30
    run:    log_cost_file("electricity", 20)
    output:
    electricity,2025-01-09,70
    water,2025-01-09,30
    '''
    if timestamp is None :
        timestamp=ntptime.time_format("short")
    filename = "/cost.txt"
    temp_filename = f"{filename}_temp.txt"
    found_entry = False

    # Create the file if it doesn't exist
    if not file_or_dir_exists(filename):
        with open(filename, 'w') as file:
            file.write("")  # Initialize an empty file

    try:
        with open(filename, 'r') as file, open(temp_filename,
                                               'w') as temp_file:
            for line in file:
                line = line.strip()
                if not line:
                    continue  # Skip empty lines

                # Manually parse the line instead of using split()
                separator1 = line.find(",")
                separator2 = line.find(",", separator1 + 1)

                if separator1 == -1 or separator2 == -1:
                    # Malformed line, write it back unchanged
                    temp_file.write(line + "\n")
                    continue

                existing_costtype = line[:separator1]
                existing_timestamp = line[separator1 + 1:separator2]
                existing_cost = line[separator2 + 1:]

                if existing_costtype == costtype and existing_timestamp == timestamp:
                    try:
                        existing_cost = float(existing_cost)
                        updated_cost = existing_cost + cost
                        line = f"{existing_costtype},{existing_timestamp},{updated_cost}"
                    except ValueError:
                        # Handle invalid cost value gracefully
                        pass
                    found_entry = True

                temp_file.write(line + "\n")

            # If no matching entry was found, append the new one
            if not found_entry:
                temp_file.write(f"{costtype},{timestamp},{cost}\n")

    except OSError:
        # If the file cannot be read, initialize it with the new data
        with open(temp_filename, 'w') as temp_file:
            temp_file.write(f"{costtype},{timestamp},{cost}\n")

    # Replace the original file with the updated file
    try:
        os.remove(filename)  # Delete the old file
        os.rename(temp_filename,
                  filename)  # Rename the temp file to the original
    except OSError as e:
        print(f"Error replacing file: {e}")
    finally:
        import gc
        gc.collect()


def get_from_dict_file(filename, costtype, date):
    """Retrieve the cost for a specific costtype and date from the file."""

    try:
        with open(filename, 'r') as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue  # Skip empty lines

                # Manually parse the line instead of using split()
                separator1 = line.find(",")
                separator2 = line.find(",", separator1 + 1)

                if separator1 == -1 or separator2 == -1:
                    # Malformed line, skip it
                    continue

                existing_costtype = line[:separator1]
                existing_timestamp = line[separator1 + 1:separator2]

                # Only check lines that match the costtype and date
                if existing_costtype == costtype and existing_timestamp == date:
                    existing_cost = line[separator2 + 1:]

                    try:
                        return float(
                            existing_cost)  # Return the cost as a float
                    except ValueError:
                        # Handle invalid cost value gracefully
                        print(f"Invalid cost value in line: {line}")
                        return None

        # If no matching entry was found, return None
        return None

    except OSError as e:
        # Handle file reading errors (e.g., file doesn't exist)
        print(f"Error reading the file: {e}")
        return None
