#! /bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:/data/myproject/venv/bin/
DESC="uwsgi daemon"
NAME=uwsgi
DAEMON=/data/myproject/venv/bin/uwsgi
CONFIGFILE=/data/myproject/cmdb/cmdb_uwsgi.ini
PIDFILE=/data/run/mysite.pid
SCRIPTNAME=/etc/init.d/$NAME
set -e
[ -x "$DAEMON" ] || exit 0
do_start() {
    $DAEMON $CONFIGFILE || echo -n "uwsgi already running"
}
do_stop() {
    $DAEMON --stop $PIDFILE || echo -n "uwsgi not running"
    rm -f $PIDFILE
    echo "$DAEMON STOPED."
}
do_reload() {
    $DAEMON --reload $PIDFILE || echo -n "uwsgi can't reload"
}
do_status() {
    ps aux|grep $DAEMON
}
case "$1" in
 status)
    echo -en "Status $NAME: \n"
    do_status
 ;;
 start)
    echo -en "Starting $NAME: \n"
    do_start
 ;;
 stop)
    echo -en "Stopping $NAME: \n"
    do_stop
 ;;
 reload|graceful)
    echo -en "Reloading $NAME: \n"
    do_reload
 ;;
 *)
    echo "Usage: $SCRIPTNAME {start|stop|reload}" >&2
    exit 3
 ;;
esac
exit 0