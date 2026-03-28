# 交互式提示性能测试

本模块不提供性能测试。

!!! info "为什么没有性能测试？"
    `prompt` 模块使用原始终端 I/O 提供交互式 CLI 提示（confirm、select、text），是一个**性能无关紧要的交互式模块** -- 执行时间完全由用户输入延迟决定，而非代码执行。

    虽然 [questionary](https://pypi.org/project/questionary/) 提供类似功能，但对交互式终端提示进行性能测试没有意义，因为瓶颈始终是人的响应时间。
