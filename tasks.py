from invoke.context import Context
from invoke.tasks import task
from pathlib import Path

import platform
import re

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
def dump(ctx:Context, output:str="code.txt"):
    root = Path(".")
    target_extensions:list[str] = [
        ".py",
    ]
    
    exclude_folders:list[str] = [
        "venv",
    ]
    
    exclude_files:list[str] = [
        "config.yaml"
    ]

    with open(output, "w", encoding="utf-8") as outfile:
        for file_path in root.rglob("*"):
            if (file_path.suffix.lower() in target_extensions):
                skip_file:bool = False
                
                if (not file_path.is_file()):
                    skip_file = True
                
                for file in exclude_files:
                    if (file in file_path.name):
                        skip_file  = True
                
                for folder in exclude_folders:
                    if (folder in str(file_path)):
                        skip_file = True
                
                if (not skip_file):
                    outfile.write(f"\n\n===== {file_path} =====\n\n")
                    outfile.write(file_path.read_text(encoding="utf-8"))
                    outfile.write("\n")

    print(f"Done! Dumped to {output}")

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