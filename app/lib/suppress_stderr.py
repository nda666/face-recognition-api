import os
import sys

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["GLOG_minloglevel"] = "3"
os.environ["GRPC_VERBOSITY"] = "ERROR"


class SuppressStderr:
    def __enter__(self):
        self.stderr_fileno = sys.stderr.fileno()
        self.old_stderr = os.dup(self.stderr_fileno)
        self.devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(self.devnull, self.stderr_fileno)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.dup2(self.old_stderr, self.stderr_fileno)
        os.close(self.devnull)
        os.close(self.old_stderr)