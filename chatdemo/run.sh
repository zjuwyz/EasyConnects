# Kill any existing 'test' sessions
tmux kill-session -t test

# Create a new session called 'test' and launch it detached
tmux -u new-session -d -s test

# Split window into two vertically
tmux split-window -v

# Split the top pane horizontally, creating two panes at the bottom
tmux selectp -t 1
tmux split-window -h

# Split the bottom pane horizontally, creating two panes at the top
tmux selectp -t 3
tmux split-window -h

tmux selectp -t 1
tmux split-window -v

tmux selectp -t 3
tmux split-window -v

tmux selectp -t 1
tmux send-keys 'which python' C-m
tmux send-keys "python chatdemo/fake_talkshow.py" C-m
#tmux send-keys "chatdemo/talkshow.sh" C-m

tmux selectp -t 2
tmux send-keys 'which python' C-m
tmux send-keys "python chatdemo/fake_chattts.py" C-m

tmux selectp -t 3
tmux send-keys 'which python' C-m
# tmux send-keys "python chatdemo/fake_easyvolcap.py" C-m
tmux send-keys "chatdemo/easyvolcap.sh" C-m

tmux selectp -t 4
tmux send-keys 'which python' C-m
#tmux send-keys "python chatdemo/fake_speaker.py" C-m
tmux send-keys "chatdemo/remote-speaker.sh"

tmux selectp -t 5
tmux send-keys 'which python' C-m
#tmux send-keys "python chatdemo/fake_flame.py" C-m
tmux send-keys "chatdemo/flame.sh" C-m

tmux selectp -t 6
tmux send-keys 'which python' C-m
tmux send-keys "python chatdemo/chatdemo_server.py" C-m

# tmux attach
