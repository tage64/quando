# Quando

A very small program to show ICS calenders in the terminal.

## Installation

* Install [pipx][2]
* Run:
    ```
    pipx install .
    ```

## Usage

The program read an [ICS calender][3] from URL.
To show a Calender, just run:
    ```
    quando show school --url https://...
    ```
Quando will remember the URL, so the next time you can just run:
    ```
    quando show school
    ```

Quando has more subcommands to list and remove calenders.
To get a complete list of all of them, run `quando --help`.

### Offline support

When reading a calender, quando will store a copy in the local cache.
If the URL can't be accessed the next time you try to read the calender, the local copy will be used instead.
This ensures you will not be completely lost without an internet connection.

[1]: https://github.com/python-poetry/poetry
[2]: https://github.com/pypa/pipx
[3]: https://docs.fileformat.com/email/ics/
