# -*- coding: utf-8 -*-
# catapult: runs python scripts in already running processes to eliminate the
# python interpreter startup time.
#
# The lexicon for sparv.saldo.annotate and sparv.saldo.compound can be pre-loaded and
# shared between processes. See the variable annotators in handle and start.
#
# Run scripts in the catapult with the c program catalaunch.

from builtins import range, object
from multiprocessing import Process, cpu_count
from decorator import decorator

import logging
import os
import re
import runpy
import socket
import sys
import traceback
import sparv.util as util

RECV_LEN = 4096

# Important to preload all modules otherwise processes will need to do
# it upon request, introducing new delays.
#
# These imports uses the __all__ variables in the __init__ files.
from sparv.util import *
from sparv import *

logging.basicConfig(format="%(process)d %(asctime)-15s %(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

"""
Splits at every space that is not preceded by a backslash.
"""
splitter = re.compile('(?<!\\\\) ')


def set_last_argument(*values):
    """
    Decorates a function f, setting its last argument(s) to the given value(s).

    Used for setting the saldo lexicons to sparv.saldo.annotate and
    sparv.saldo.compound, and the process "dictionary" to sparv.malt.maltparse.

    The decorator module is used to give the same signature and
    docstring to the function, which is exploited in sparv.util.run.
    """
    @decorator
    def inner(f, *args, **kwargs):
        args = list(args)
        for v in values:
            args.pop()
        for v in values:
            args.append(v)
        f(*args, **kwargs)
    return inner


def handle(client_sock, verbose, annotators):
    """
    Handle a client: parse the arguments, change to the relevant
    directory, then run the script. Stdout and stderr are directed
    to /dev/null or to the client socket.
    """

    def chunk_send(msg):
        """
        Sends a message chunk until it is totally received in the other end
        """
        msg = msg.encode(util.UTF8)
        while len(msg) > 0:
            sent = client_sock.send(msg)
            if sent == 0:
                raise RuntimeError("socket connection broken")
            msg = msg[sent:]

    def set_stdout_stderr():
        """
        Put stdout and stderr to the client_sock, if verbose.
        Returns the clean-up handler.
        """

        class Writer(object):
            def write(self, msg):
                log.debug(msg)
                if verbose:
                    chunk_send(msg)

            def flush(self):
                pass

        orig_stds = sys.stdout, sys.stderr
        w = Writer()
        sys.stdout = w
        sys.stderr = w

        def cleanup():
            """
            Restores stdout and stderr
            """
            sys.stdout = orig_stds[0]
            sys.stderr = orig_stds[1]
            client_sock.close()

        return cleanup

    # Receive data
    data = b""
    new_data = None
    # Message is terminated with a lone \
    while new_data is None or not new_data.endswith(b'\\'):
        new_data = client_sock.recv(RECV_LEN)
        log.debug("Received %s", new_data)
        data += new_data
        if len(new_data) == 0:
            log.warning("Received null!")
            chunk_send("Error when receiving: got an empty message")
            return

    # Drop the terminating \
    data = data[0:-1]

    # Split arguments on spaces, and replace '\ ' to ' ' and \\ to \
    args = [arg.replace('\\ ', ' ').replace('\\\\', '\\')
            for arg in re.split(splitter, data.decode(util.UTF8))]
    log.debug("Args: %s", args)

    ### PING? ###
    if len(args) == 2 and args[1] == "PING":
        log.info("Ping requested")
        chunk_send("PONG")
        return

    # If the first argument is -m, the following argument is a module
    # name instead of a script name
    module_flag = len(args) > 2 and args[1] == '-m'

    if module_flag:
        args.pop(1)

    if len(args) > 1:

        # First argument is the pwd of the caller
        old_pwd = os.getcwd()
        pwd = args.pop(0)

        log.info('Running %s', args[0])
        log.debug('with arguments: %s', ' '.join(args[1:]))
        log.debug('in directory %s', pwd)

        # Set stdout and stderr, which returns the cleaup function
        cleanup = set_stdout_stderr()

        # Run the command
        try:
            sys.argv = args
            os.chdir(pwd)
            if module_flag:

                annotator = annotators.get(args[0], None)

                if not annotator:
                    # some of the annotators require two arguments
                    annotator = annotators.get((args[0], args[1]), None)
                    if annotator:
                        # skip the first argument now
                        sys.argv = args[0]
                        sys.argv.extend(args[2:])

                if annotator:
                    util.run.main(annotator)
                else:
                    runpy.run_module(args[0], run_name='__main__')
            else:
                runpy.run_path(args[0], run_name='__main__')
        except (ImportError, IOError):
            # If file does not exist, send the error message
            chunk_send("%s\n" % sys.exc_info()[1])
            cleanup()
            log.exception("File does not exist")
        except:
            # Send other errors, and if verbose, send tracebacks
            chunk_send("%s\n" % sys.exc_info()[1])
            traceback.print_exception(*sys.exc_info())
            cleanup()
            log.exception("Unknown error")
        else:
            cleanup()

        os.chdir(old_pwd)

        # Run the cleanup function if there is one (only used with malt)
        annotators.get((args[0], 'cleanup'), lambda: None)()

        log.info('Completed %s', args[0])

    else:
        log.info('Cannot handle %s', data)
        chunk_send('Cannot handle %s\n' % data)


def worker(server_socket, verbose, annotators, malt_args=None, swener_args=None):
    """
    Workers listen to the socket server, and handle incoming requests

    Each process starts an own maltparser process, because they are
    cheap and cannot serve multiple clients at the same time.
    """

    if malt_args:

        process_dict = dict(process=None, restart=True)

        def start_malt():
            if process_dict['process'] is None or process_dict['restart']:

                old_process = process_dict['process']
                old_process and util.system.kill_process(old_process)

                malt_process = malt.maltstart(**malt_args)
                if verbose:
                    log.info('(Re)started malt process: %s', malt_process)
                process_dict['process'] = malt_process
                annotators['sparv.malt'] = set_last_argument(process_dict)(malt.maltparse)

            elif verbose:
                log.info("Not restarting malt this time")

        start_malt()
        annotators['sparv.malt', 'cleanup'] = start_malt

    if swener_args:
        process_dict = dict(process=None, restart=True)

        def start_swener():
            if process_dict['process'] is None or process_dict['restart']:

                old_process = process_dict['process']
                old_process and util.system.kill_process(old_process)

                swener_process = swener.swenerstart(**swener_args)
                if verbose:
                    log.info('(Re)started SweNER process: %s', swener_process)
                process_dict['process'] = swener_process
                annotators['sparv.swener'] = set_last_argument(process_dict)(swener.tag_ne)

            elif verbose:
                log.info("Not restarting SweNER this time")

        start_swener()
        annotators['sparv.swener', 'cleanup'] = start_swener

    if verbose:
        log.info("Worker running!")

    while True:
        client_sock, addr = server_socket.accept()
        try:
            handle(client_sock, verbose, annotators)
        except:
            log.exception('Error in handling code')
            traceback.print_exception(*sys.exc_info())
        client_sock.close()


def start(socket_path, processes=1, verbose='false',
          saldo_model=None, compound_model=None, stats_model=None,
          dalin_model=None, swedberg_model=None, blingbring_model=None,
          malt_jar=None, malt_model=None, malt_encoding=util.UTF8,
          sentiment_model=None, swefn_model=None, swener=False,
          swener_encoding=util.UTF8):
    """
    Starts a catapult on a socket file, using a number of processes.

    If verbose is false, all stdout and stderr programs produce is
    piped to /dev/null, otherwise it is sent to the client. The
    computation is done by the catapult processes, however.
    Regardless of what verbose is, client errors should be reported
    both in the catapult and to the client.

    The saldo model and compound model can be pre-loaded and shared in
    memory between processes.

    Start processes using catalaunch.
    """

    if os.path.exists(socket_path):
        log.error('socket %s already exists', socket_path)
        exit(1)

    verbose = verbose.lower() == 'true'

    log.info('Verbose: %s', verbose)

    # If processes does not contain an int, set it to the number of processors
    try:
        processes = int(processes)
    except:
        processes = cpu_count()

    # Start the socket
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_socket.bind(socket_path)
    server_socket.listen(processes)

    # The dictionary of functions with saved lexica, indexed by module name strings
    annotators = {}

    # Load Saldo and older lexicons
    lexicons = [m for m in [saldo_model, dalin_model, swedberg_model] if m]
    if lexicons:
        lexicon_dict = {}
        for lexicon in lexicons:
            lexicon_dict[os.path.basename(lexicon).rstrip(".pickle")] = saldo.SaldoLexicon(lexicon)
        annotators['sparv.saldo'] = set_last_argument(lexicon_dict)(saldo.annotate)

    if stats_model and compound_model:
        annotators['sparv.compound'] = set_last_argument(
            compound.SaldoCompLexicon(compound_model),
            compound.StatsLexicon(stats_model))(compound.annotate)

    elif compound_model:
        annotators['sparv.compound_simple'] = set_last_argument(
            compound_simple.SaldoLexicon(compound_model))(compound_simple.annotate)

    # if blingbring_model:
    #     annotators['sparv.lexical_classes'] = set_last_argument(
    #         util.PickledLexicon(blingbring_model))(lexical_classes.annotate_bb_words)

    # if swefn_model:
    #     annotators['sparv.lexical_classes'] = set_last_argument(
    #         util.PickledLexicon(swefn_model))(lexical_classes.annotate_swefn_words)

    if sentiment_model:
        annotators['sparv.sentiment'] = set_last_argument(
            util.PickledLexicon(sentiment_model))(sentiment.sentiment)

    # if models_1700s:
    #     models = models_1700s.split()
    #     lexicons = [saldo.SaldoLexicon(lex) for lex in models]
    #     annotators[('sparv.fsv', '--annotate_fallback')] = set_last_argument(lexicons)(fsv.annotate_fallback)
    #     annotators[('sparv.fsv', '--annotate_full')] = set_last_argument(lexicons)(fsv.annotate_full)

    if verbose:
        log.info('Loaded annotators: %s', list(annotators.keys()))

    if malt_jar and malt_model:
        malt_args = dict(maltjar=malt_jar, model=malt_model,
                         encoding=malt_encoding, send_empty_sentence=True)
    else:
        malt_args = None

    if swener:
        swener_args = dict(stdin="", encoding=swener_encoding, verbose=True)
    else:
        swener_args = None

    # Start processes-1 workers
    workers = [Process(target=worker, args=[server_socket, verbose, annotators, malt_args])
               for i in range(processes - 1)]

    for p in workers:
        p.start()

    # Additionally, let this thread be worker 0
    worker(server_socket, verbose, annotators, malt_args, swener_args)

if __name__ == '__main__':
    util.run.main(start)
