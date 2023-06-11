load("@rules_python//python:defs.bzl", "py_library", "py_test")


def gen_py_test_base(name, args):

    py_test(
        name = name.replace("/", "-"),
        srcs = [name + "/test.py"],
        main = name + "/test.py",
        data = native.glob([name + "/**"]),
        deps = ["//:unknownlib"],
        args = args,
    )


def gen_py_test(name):

    gen_py_test_base(name, [])


def gen_scheme_test(name):

    gen_py_test_base(name, ["test/" + name + "/cfg.yaml"])