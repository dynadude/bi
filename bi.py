#!/usr/bin/env python3

import tempfile
import os
import sys
import math
import getpass
import shutil
from typing import TypeVar
T = TypeVar('T')


USER_BI_DIR = os.path.join(tempfile.gettempdir(), f"bi-{getpass.getuser()}")
CONTEXT_FILE_PATH = os.path.join(USER_BI_DIR, 'context')
LOG_FILE_PATH = os.path.join(USER_BI_DIR, 'log')


def print_help_text() -> None:
    print(
        '''The bi python script performs a git-bisect-like operation on the contents of a text file, treating each line as a 'revision' to test.
'''
    )


def is_empty(dir: str) -> bool:
    for _ in os.scandir(dir):
        return False

    return True


def start_command(script_args: list[str]) -> None:
    original_context_file = script_args[2]
    # remove empty lines
    context = get_context(original_context_file)

    if len(context) < 1:
        print(
            'Specified context file does not contain non-empty lines. Aborting...')
        return

    # Create the user bi dir if it does not exist, but abort if it exists but isn't a directory (most likely a regular file)
    if not os.path.isdir(USER_BI_DIR):
        if os.path.exists(USER_BI_DIR):
            print(
                f"Path {USER_BI_DIR} exists but is not a directory. Please remove it manually. Aborting...")
            return

        os.mkdir(USER_BI_DIR)

    # Prompt the user to make sure they approve of overwriting the previous contents of their user bi dir if it isn't empty
    if not is_empty(USER_BI_DIR):
        # TODO: prompt user about overwriting the directory
        print('dir is NOT empty!!!!!')
        recreate_dir(USER_BI_DIR)

    write_lines_to_file(CONTEXT_FILE_PATH, context)
    write_lines_to_file(LOG_FILE_PATH, [])


def status_command() -> None:
    # TODO: notify and exit when there's only a bad/good line
    print_current_line_message()


def mark_line_command(script_args: list[str]) -> None:
    operation = script_args[1]
    # TODO: do not print status when there's only a bad/good line or there aren't any
    marked_line_index = None
    if len(script_args) > 2:
        marked_line_index = get_context_line_index(script_args[2])
    else:
        marked_line_index = get_current_line_index()

    current_line = get_context_line(marked_line_index)
    write_operation_to_log(operation, marked_line_index)
    print(
        f"Line '{current_line}' of index {marked_line_index} has been marked as {operation}")

    print_current_line_message()


def reset_command() -> None:
    if os.path.isdir(USER_BI_DIR):
        recreate_dir(USER_BI_DIR)
        print(f"Successfully recreated {USER_BI_DIR}")
    elif os.path.exists(USER_BI_DIR):
        print(
            f"Path {USER_BI_DIR} exists but is not a directory. Please remove it manually. Aborting...")
        return
    else:
        print(f"Nothing to do as {USER_BI_DIR} does not exist yet")


def get_context(path: str = CONTEXT_FILE_PATH) -> list[str]:
    return list(filter(None, get_lines_in_file(path)))


def get_log(path: str = LOG_FILE_PATH) -> list[tuple[str, int]]:
    log_lines = list(filter(lambda x: not x.startswith('#'), get_raw_log()))
    log_operations: list[tuple[str, int]] = []
    for line in log_lines:
        words = line.strip().split()

        operation = words[0]
        context_line_index = int(words[1])

        log_operations.append((operation, context_line_index))
    return log_operations


def get_raw_log(path: str = LOG_FILE_PATH) -> list[str]:
    """
        Get all log file lines, including comment lines
    """
    return get_context(path)


def get_lines_in_file(path: str) -> list[str]:
    with open(path) as f:
        return f.read().splitlines()


def write_operation_to_log(operation: str, context_line_index: int) -> None:
    # the raw_log variable contains comment lines
    raw_log = get_raw_log()

    raw_log.append(
        f"# {operation}: [{context_line_index}] {get_context_line(context_line_index)}")
    raw_log.append(f"{operation} {context_line_index}")

    write_lines_to_file(LOG_FILE_PATH, raw_log)


def write_lines_to_file(path: str, lines: list[str]) -> None:
    with open(path, 'w') as f:
        # TODO: platform-agnostic line-breaks
        f.writelines(map(lambda s: s + '\n', lines))


def recreate_dir(path: str) -> None:
    shutil.rmtree(path)
    os.mkdir(path)


def get_current_line_index(filtered_context_indices: list[int] | None = None) -> int:
    if filtered_context_indices is None:
        # typical initial content: [0, 1, 2, 3, ...]
        filtered_context_indices = get_filtered_context_indices(get_log())

    # TODO: remove print
    print(len(filtered_context_indices))

    # TODO: take skipped lines into account (raise new type of exception)
    current_line_index_filtered_index = math.floor(
        (len(filtered_context_indices)) / 2)
    return filtered_context_indices[current_line_index_filtered_index]


def get_filtered_context_indices(log: list[tuple[str, int]] | None = None) -> list[int]:
    if log is None:
        log = get_log()

    # TODO: bound check for first line being old or last line being new
    full_context = get_context()
    # typical initial content: [0, 1, 2, 3, ...]
    filtered_context_indices: list[int] = list(range(len(full_context)))

    for operation in log:
        operation_type = operation[0]
        context_line_index = operation[1]

        if not context_line_index in filtered_context_indices:
            continue

        match operation_type:
            case 'bad' | 'new':
                remove_before(filtered_context_indices, context_line_index)
            case 'good' | 'old':
                remove_after(filtered_context_indices, context_line_index)
                # TODO: test without this
                filtered_context_indices.pop(-1)
            case _:
                pass

    return filtered_context_indices


def remove_before(lst: list[T], element: T) -> None:
    original_length = len(lst)
    for i in range(original_length):  # pyright: ignore[reportUnusedVariable]
        if lst[0] == element:
            return

        lst.pop(0)


def remove_after(lst: list[T], element: T) -> None:
    original_length = len(lst)
    for i in range(original_length):  # pyright: ignore[reportUnusedVariable]
        if lst[-1] == element:
            return

        lst.pop(-1)


def print_current_line_message(filtered_context_indices: list[int] | None = None) -> None:
    if filtered_context_indices is None:
        # typical initial content: [0, 1, 2, 3, ...]
        filtered_context_indices = get_filtered_context_indices(get_log())

    marked_line_index = get_current_line_index(
        filtered_context_indices)
    current_line = get_context_line(marked_line_index)
    if len(filtered_context_indices) == 1:
        print(
            f"Line '{current_line}' of index {marked_line_index} is the first bad/new line!")
        return

    print(
        f"Currently on line '{current_line}' of index {marked_line_index}")


def get_context_line_index(line: str) -> int:
    context = get_context()
    for i in range(len(context)):
        context_line = context[i]
        if context_line.strip() == line.strip():
            return i

    raise FileNotFoundError('No context line found for the given content')


def get_context_line(index: int) -> str:
    return get_context()[index]


def main() -> None:
    script_args = sys.argv

    # the first value in the list is the script itself
    if len(script_args) <= 1:
        print_help_text()

    operation = script_args[1]
    match operation:
        case 'start':
            start_command(script_args)
        case 'status':
            status_command()
        case 'good' | 'old' | 'bad' | 'new' | 'skip':
            mark_line_command(script_args)
        case 'reset':
            reset_command()
        case 'visualize' | 'view':
            pass
        case 'replay':
            pass
        case 'log':
            pass
        case 'next':
            pass
        case 'help' | _:
            print_help_text()


if __name__ == '__main__':
    main()
