
import numpy as np
import os
exp_code=[]
flame_pose_params=[]

for i in range(12):
    
    npz = np.load(f"data/blink_flame/{i:06d}.npz")
    exp_code.append(npz['exp_code'])
    flame_pose_params.append(npz['flame_pose_params'])
    
for i in range(12):
    if i > 0:
        exp_code[i] -= exp_code[0]
        flame_pose_params[i] -= flame_pose_params[0]
        
blink_diff = exp_code[1:]
np.savez("data/blink_flame/blink_diff.npz", blink_diff=blink_diff)