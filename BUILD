load("@rules_python//python:defs.bzl", "py_library", "py_test")

py_library(
    name = "unknownlib",
    srcs = glob(["lib/unknownlib/**/*.py"]),
    deps = [],
    visibility = ["//visibility:public"],
    imports = ["lib"],
)