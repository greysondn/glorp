from invoke.context import Context
from invoke.tasks import task

import platform

@task
def build(ctx:Context):
    match platform.system():
        case _:
            print(f"Running on unimplemented platform: {platform.system()}")

@task
def clean(ctx:Context):
    match platform.system():
        case _:
            print(f"Running on unimplemented platform: {platform.system()}")

@task
def test(ctx:Context):
    match platform.system():
        case("Windows"):
            ctx.run("pytest --showlocals -s --timeout=10 --timeout-method=thread")
        case _:
            print(f"Running on unimplemented platform: {platform.system()}")

@task
def prerelease(ctx:Context):
    match platform.system():
        case _:
            print(f"Running on unimplemented platform: {platform.system()}")

@task
def release(ctx:Context):
    match platform.system():
        case _:
            print(f"Running on unimplemented platform: {platform.system()}")