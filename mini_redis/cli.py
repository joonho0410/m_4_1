"""REPL front-end: parses a line into a command, dispatches to Store, formats output."""

import shlex

from .store import OOMError, Store

PROMPT = "mini-redis> "


def fmt_ok():
    return "OK"


def fmt_nil():
    return "(nil)"


def fmt_int(n):
    return f"(integer) {n}"


def fmt_err(msg):
    return f"(error) {msg}"


def fmt_bulk(s):
    return f'"{s}"'


def fmt_array(items):
    if not items:
        return "(empty array)"
    return "\n".join(fmt_bulk(item) for item in items)


ERR_UNKNOWN = "ERR unknown command '{cmd}'"
ERR_ARGS = "ERR wrong number of arguments for '{cmd}' command"
ERR_NOT_INT = "ERR value is not an integer or out of range"
ERR_OOM = "OOM command not allowed when used_memory > 'maxmemory'"


def _parse_int(token):
    try:
        return int(token)
    except ValueError:
        return None


class MiniRedisCLI:
    def __init__(self, store=None):
        self.store = store or Store()

    def execute(self, line):
        """Parse + dispatch one line, returning the output string (or None to
        signal the REPL should exit)."""
        line = line.strip()
        if not line:
            return ""

        try:
            tokens = shlex.split(line)
        except ValueError:
            return fmt_err("ERR unbalanced quotes in request")

        if not tokens:
            return ""

        cmd = tokens[0].upper()
        args = tokens[1:]

        if cmd in ("EXIT", "QUIT"):
            return None

        self.store.purge_expired()

        handler = getattr(self, f"_cmd_{cmd.lower()}", None)
        if handler is None:
            return fmt_err(ERR_UNKNOWN.format(cmd=tokens[0]))
        return handler(cmd, args)

    # -- string commands ----------------------------------------------------

    def _cmd_set(self, cmd, args):
        if len(args) != 2:
            return fmt_err(ERR_ARGS.format(cmd="set"))
        key, value = args
        try:
            self.store.set(key, value)
        except OOMError:
            return fmt_err(ERR_OOM)
        return fmt_ok()

    def _cmd_get(self, cmd, args):
        if len(args) != 1:
            return fmt_err(ERR_ARGS.format(cmd="get"))
        value = self.store.get(args[0])
        return fmt_nil() if value is None else fmt_bulk(value)

    def _cmd_del(self, cmd, args):
        if len(args) != 1:
            return fmt_err(ERR_ARGS.format(cmd="del"))
        return fmt_int(1 if self.store.delete(args[0]) else 0)

    def _cmd_exists(self, cmd, args):
        if len(args) != 1:
            return fmt_err(ERR_ARGS.format(cmd="exists"))
        return fmt_int(1 if self.store.exists(args[0]) else 0)

    def _cmd_dbsize(self, cmd, args):
        if len(args) != 0:
            return fmt_err(ERR_ARGS.format(cmd="dbsize"))
        return fmt_int(self.store.dbsize())

    def _cmd_keys(self, cmd, args):
        if len(args) != 0:
            return fmt_err(ERR_ARGS.format(cmd="keys"))
        return fmt_array(self.store.keys())

    # -- TTL commands ------------------------------------------------------

    def _cmd_expire(self, cmd, args):
        if len(args) != 2:
            return fmt_err(ERR_ARGS.format(cmd="expire"))
        key, seconds_tok = args
        seconds = _parse_int(seconds_tok)
        if seconds is None:
            return fmt_err(ERR_NOT_INT)
        return fmt_int(self.store.expire(key, seconds))

    def _cmd_ttl(self, cmd, args):
        if len(args) != 1:
            return fmt_err(ERR_ARGS.format(cmd="ttl"))
        return fmt_int(self.store.ttl(args[0]))

    # -- memory / config commands --------------------------------------------

    def _cmd_config(self, cmd, args):
        if len(args) != 3 or args[0].upper() != "SET" or args[1].lower() != "maxmemory":
            return fmt_err(ERR_ARGS.format(cmd="config|set"))
        num_bytes = _parse_int(args[2])
        if num_bytes is None or num_bytes < 0:
            return fmt_err(ERR_NOT_INT)
        self.store.config_set_maxmemory(num_bytes)
        return fmt_ok()

    def _cmd_info(self, cmd, args):
        if len(args) != 1 or args[0].lower() != "memory":
            return fmt_err(ERR_ARGS.format(cmd="info"))
        info = self.store.info_memory()
        return (
            f"used_memory:{info['used_memory']}\n"
            f"maxmemory:{info['maxmemory']}\n"
            f"evicted_keys:{info['evicted_keys']}"
        )

    # -- REPL loop ----------------------------------------------------------

    def run(self):
        print("Mini Redis - type 'exit' or 'quit' to leave.")
        while True:
            try:
                line = input(PROMPT)
            except (EOFError, KeyboardInterrupt):
                print()
                break
            output = self.execute(line)
            if output is None:
                break
            if output != "":
                print(output)
