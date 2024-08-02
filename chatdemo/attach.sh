while :
do
    tmux has-session -t test 2>/dev/null
    if [ $? = 0 ]; then
        tmux -u attach-session -t test
        sleep 1
    else
        echo "Session 'test' does not exist. Trying again"
        sleep 1
    fi
done
