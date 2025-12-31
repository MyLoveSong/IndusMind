import subprocess
import json
import re


def test_local_generate_runs():
    cmd = (
        "/home/xzy/anaconda3/envs/XZY/bin/python /home/xzy/QWEN3-8B/tools/local_generate.py "
        "--prompt \"请用中文简短介绍量子计算的主要应用场景：\" --max_new_tokens 128"
    )
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300)
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    assert proc.returncode == 0, f"generation failed: {stderr}"
    # output should be non-empty and contain CJK characters
    assert len(stdout) > 10
    assert re.search(r"[\u4e00-\u9fff]", stdout)


