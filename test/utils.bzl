load("@rules_python//python:defs.bzl", "py_library", "py_test")

def gen_py_test(name):

    py_test(
        name = name.replace("/", "-"),
        srcs = [name + "/test.py"],
        main = name + "/test.py",
        data = native.glob([name + "/**"]),
        deps = ["//:unknownlib"]
    )