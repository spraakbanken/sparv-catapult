/*

  catalaunch: starts processes on the catapult

  First argument is the socket file, remaining arguments are as to the python
  command, supporting paths to scripts, and modules with -m. Examples:

  catalaunch catapult.sockfile -m sb.saldo --xml_to_pickle minisaldo.xml
  catalaunch catapult.sockfile script.py any arguments

  If the catapult is verbose, then the script's stdout and stderr will be
  printed on stdout.

  The catalaunch process terminates when the socket exits.

  The internal protocol first sends the current working directory, and then the
  command line arguments, separated by spaces. For this reason, spaces in
  arguments are escaped with backslash, so therefore backslashes are escaped by
  backslashes.  The message is terminated with a backlash without any following
  character.

  If the messages exceed the sending length, they are chunked.

  However, this is not implemented for sending the working directory, so if it
  is too long (exceeds PWD_LEN), it will be cut. Try not to use paths exceeding
  2000 characters.

*/
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>

#define PWD_LEN 2048
#define SEND_LEN 4096
#define RECV_LEN 4096

int main(int argc, char **argv)
{
    // A script needs to be specified
    if (argc <= 2) {
        printf("Example usage:\n\n\t%s sockfile -m sb.noop --flags flag\n", argv[0]);
        return -1;
    }

    int s, len;
    struct sockaddr_un remote;

    // Open the socket
    if ((s = socket(AF_UNIX, SOCK_STREAM, 0)) == -1) {
        perror("socket: Opening the socket failed");
        exit(1);
    }

    // Try to connect
    remote.sun_family = AF_UNIX;
    strcpy(remote.sun_path, argv[1]);
    len = strlen(remote.sun_path) + sizeof(remote.sun_family);
    if (connect(s, (struct sockaddr *)&remote, len) == -1) {
        perror("connect: Connecting to socket failed");
        exit(1);
    }

    char msg[SEND_LEN], pwd[PWD_LEN], *c;
    int p=0;

    // The cwd is first in the message
    getcwd(pwd,PWD_LEN);
    for(c=pwd; *c; ++c) {
        // escape backslash and space
        if (*c == ' ' || *c == '\\')  msg[p++] = '\\';
        msg[p++] = *c;
    }

    // Then all args are copied to msg
    // The 0th argument is skipped as it contains the executable name
    int arg;
    for (arg=2; arg < argc; ++arg) {
        // add a space between arguments
        msg[p++] = ' ';
        // copy argument #arg
        for (c=argv[arg]; *c; ++c) {
            // escape backslash and space
            if (*c == ' ' || *c == '\\')  msg[p++] = '\\';
            msg[p++] = *c;

            // send this part of the message if we're about to exceed
            // the buffer length
            if (p >= SEND_LEN-4) {
                if (send(s, msg, p, 0) < 0) {
                    perror("send: Sending error");
                    return -1;
                }
                p = 0; // reset position to start
            }
        }
    }

    // Send the terminating backsalsh.
    msg[p++] = '\\';

    // send remaining part of the message
    if (send(s, msg, p, 0) < 0) {
        perror("send: Sending error");
        return -1;
    }

    // Receiving
    char str[RECV_LEN];
    int n;
    while (n = recv(s, str, RECV_LEN, 0), n > 0) {
        str[n] = '\0';
        printf("%s", str);
    }
    fflush(stdout);

    if (n < 0) {
        perror("recv: Receiving error");
    }

    close(s);

    return 0;
}
