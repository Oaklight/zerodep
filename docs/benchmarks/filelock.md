# 文件锁性能测试

`filelock` 模块未提供正式的性能测试。锁操作直接委托给操作系统级别的系统调用（`fcntl.flock` / `msvcrt.locking`），额外开销可忽略不计。
