#!/usr/bin/env python3

import tempfile
import os
import sys
import math
import getpass
import shutil
import pydoc
from typing import TypeVar
T = TypeVar('T')


USER_BI_DIR = os.path.join(tempfile.gettempdir(), f"bi-{getpass.getuser()}")
CONTEXT_FILE_PATH = os.path.join(USER_BI_DIR, 'context')
LOG_FILE_PATH = os.path.join(USER_BI_DIR, 'log')


class InvalidOperationTypeError(Exception):
    pass


class FirstLineOldError(Exception):
    pass


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

    # Includes prompting the user if the bi dir is not empty
    reset_command()

    write_lines_to_file(CONTEXT_FILE_PATH, context)
    write_lines_to_file(LOG_FILE_PATH, [])

    print_current_line_message()


def status_command() -> None:
    verify_marked_lines_are_valid()

    print_current_line_message()


def mark_line_command(script_args: list[str]) -> None:
    operation = script_args[1]
    marked_line_index = None
    if len(script_args) > 2:
        marked_line_index = get_context_line_index(script_args[2])
    else:
        marked_line_index = get_current_line_index()

    current_line = get_context_line(marked_line_index)
    write_operation_to_log(operation, marked_line_index)
    verify_marked_lines_are_valid()

    print(
        f"Line '{current_line}' of index {marked_line_index} has been marked as {operation}")

    print_current_line_message()


def reset_command() -> None:
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

    print(f"Successfully recreated {USER_BI_DIR}")


def visualize_command() -> None:
    context = get_context()
    filtered_context_indices = get_filtered_context_indices()
    current_line_index = get_current_line_index(filtered_context_indices)
    filtered_context_lines: list[str] = []

    context[current_line_index] += ' (HEAD)'
    for index in filtered_context_indices:
        filtered_context_lines.append(context[index])

    joined_string = os.linesep.join(filtered_context_lines)
    # The + 1 is there so that the previous terminal line would need to be visible to avoid paging
    if shutil.get_terminal_size().lines <= len(filtered_context_lines) + 1:
        pydoc.pager(joined_string)
    else:
        print(joined_string)


def replay_command(script_args: list[str]) -> None:
    supplied_log_file = script_args[2]
    raw_log = get_raw_log(supplied_log_file)

    verify_marked_lines_are_valid(get_log(supplied_log_file))

    write_lines_to_file(LOG_FILE_PATH, raw_log)

    print(f"Successfully replayed from file {supplied_log_file}")

    print_current_line_message()


def log_command() -> None:
    print(os.linesep.join(get_raw_log()))


def verify_marked_lines_are_valid(log: list[tuple[str, int]] | None = None) -> None:
    if log is None:
        log = get_log()

    context = get_context()
    # typical content: [0, 1, 2, 3, ...]
    context_indices: list[int] = list(range(len(context)))

    existing_markings: dict[int, str] = dict()
    for operation in log:
        operation_type = operation[0]
        context_line_index = operation[1]

        # Verify that the operation type is valid
        match operation_type:
            case 'good' | 'old' | 'bad' | 'new' | 'skip':
                pass
            case _:
                raise InvalidOperationTypeError(
                    f"Operation type '{operation_type}' is invalid")

        # Verify that all marked lines correspond to real lines in the context
        if context_line_index not in context_indices:
            raise FileNotFoundError(
                f"Context does not contain line of index {context_line_index}")

        # Verify that there are no conflicting markings for the same line
        if context_line_index in existing_markings and not are_operation_types_equivalent(operation_type, existing_markings[context_line_index]):
            context_line = get_context_line(context_line_index)
            raise FileExistsError(
                f"Line '{context_line}' of index {context_line_index} has been marked as both {existing_markings[context_line_index]} and {operation_type}")

        existing_markings[context_line_index] = operation_type


def are_operation_types_equivalent(first_type: str, second_type: str) -> bool:
    if first_type == second_type:
        return True

    if first_type == 'good' and second_type == 'old' or \
       first_type == 'old' and second_type == 'good':
        return True

    if first_type == 'bad' and second_type == 'new' or \
       first_type == 'new' and second_type == 'bad':
        return True

    return False


def get_context(path: str = CONTEXT_FILE_PATH) -> list[str]:
    return list(filter(None, get_lines_in_file(path)))


def get_log(path: str = LOG_FILE_PATH) -> list[tuple[str, int]]:
    log_lines = list(
        filter(lambda x: not x.startswith('#'), get_raw_log(path)))
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
        f.writelines(map(lambda s: s + os.linesep, lines))


def recreate_dir(path: str) -> None:
    shutil.rmtree(path)
    os.mkdir(path)


def get_current_line_index(filtered_context_indices: list[int] | None = None) -> int:
    if filtered_context_indices is None:
        # typical initial content: [0, 1, 2, 3, ...]
        filtered_context_indices = get_filtered_context_indices()

    # TODO: take skipped lines into account (raise new type of exception)
    current_line_index_filtered_index = math.floor(
        (len(filtered_context_indices)) / 2)
    return filtered_context_indices[current_line_index_filtered_index]


def get_filtered_context_indices(log: list[tuple[str, int]] | None = None) -> list[int]:
    if log is None:
        log = get_log()

    # TODO: bound check for first line being old
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
                # Only remove lines BEFORE new lines, not the new line itself
                remove_before(filtered_context_indices, context_line_index)
            case 'good' | 'old':
                remove_after(filtered_context_indices, context_line_index)
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
        # typical content: [0, 1, 2, 3, ...]
        filtered_context_indices = get_filtered_context_indices(get_log())

    current_line_index = get_current_line_index(
        filtered_context_indices)
    current_line = get_context_line(current_line_index)
    if len(filtered_context_indices) == 1:
        print(
            f"Line '{current_line}' of index {current_line_index} is the first bad/new line!")
        return

    approximate_step_count = math.ceil(
        math.log(len(filtered_context_indices), 2))
    print(f"{len(filtered_context_indices)} lines left to test after this (roughly {approximate_step_count} steps)")
    print(
        f"Currently on line '{current_line}' of index {current_line_index}")


def get_context_line_index(line: str) -> int:
    context = get_context()
    for i in range(len(context)):
        context_line = context[i]
        if context_line.strip() == line.strip():
            return i

    raise FileNotFoundError('No context line found for the given content')


def get_context_line(index: int) -> str:
    return get_context()[index]


def get_operation_type_at_index(index: int) -> str | None:
    log = get_log()
    for operation in log:
        operation_type = operation[0]
        context_line_index = operation[1]

        if context_line_index == index:
            return operation_type

    return None


def main() -> None:
    script_args = sys.argv

    # the first value in the list is the script itself
    if len(script_args) <= 1:
        print_help_text()

    operation = script_args[1]
    match operation:
        case 'start' | 'reset' | 'help':
            pass
        case _:
            if not os.path.isdir(USER_BI_DIR) or \
               not os.path.isfile(CONTEXT_FILE_PATH) or \
               not os.path.isfile(LOG_FILE_PATH):
                print(
                    "Bi hasn't been started. Please run 'bi start file_path' or run 'bi help' for directions")
                return

    match operation:
        case 'start':
            start_command(script_args)
        case 'status':
            status_command()
        case 'good' | 'old' | 'bad' | 'new' | 'skip':
            mark_line_command(script_args)
        case 'reset':
            reset_command()
        case 'visualize' | 'visualise' | 'view':
            visualize_command()
        case 'replay':
            replay_command(script_args)
        case 'log':
            log_command()
        case 'help' | _:
            print_help_text()


if __name__ == '__main__':
    main()
