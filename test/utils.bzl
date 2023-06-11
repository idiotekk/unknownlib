load("@rules_python//python:defs.bzl", "py_library", "py_test")


def gen_py_test_base(name, args=[], extra_data=[]):

    py_test(
        name = name.replace("/", "-"),
        srcs = [name + "/test.py"],
        main = name + "/test.py",
        data = native.glob([
            name + "/**",
        ]) + extra_data,
        deps = ["//:unknownlib"],
        args = args,
    )


def gen_evm_test(name):

    gen_py_test_base(
        "evm/" + name,
        extra_data = native.glob(["evm/.private/**"])
    )


def gen_scheme_test(name):

    gen_py_test_base(
        "scheme/" + name,
        args = ["test/scheme/" + name + "/cfg.yaml"]
    )