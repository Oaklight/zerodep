# File Lock Benchmark

No formal benchmark is provided for the `filelock` module. The locking operations delegate directly to OS-level syscalls (`fcntl.flock` / `msvcrt.locking`) and add negligible overhead.
