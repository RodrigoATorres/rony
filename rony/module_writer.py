import click
import os
import json
from jinja2 import Template
import subprocess
from unidiff import PatchSet


class RonyModule:

    module_name = "CHANGEME"
    module_desc = "Module Description"
    module_version = "0.0.1"
    developers = ["rony@a3data.com.br"]
    instructions = """
    Intructions test
    """
    exclude_dirs = ["__pycache__"]
    exclude_filenames = [".ronyignore"]
    exclude_filepaths = []

    def __init__(
        self, local_path: str, autoconfirm: bool = False, info: dict = {}
    ) -> None:

        #
        self.local_path = local_path
        self.autoconfirm = autoconfirm
        self.info = info

        #
        self.get_module_inputs()
        self.add_module()

    def add_module(self):

        self.get_files_to_add()
        self.custom_file_manipulation()
        self.apply()

    def get_module_inputs(self):

        self.user_inputs = {}

    def get_files_to_add(self) -> None:
        """[summary]

        Returns:
            [type]: [description]
        """

        self.files_to_add = {}
        self.dirs_to_create = []

        for dir_path, dirs, files in os.walk(self.module_dir):

            dir_name = os.path.basename(dir_path)
            rel_path = os.path.relpath(dir_path, self.module_dir)
            local_dir_path = os.path.join(self.local_path, rel_path)

            if dir_name in self.exclude_dirs:
                continue

            for d in dirs:
                if d in self.exclude_dirs:
                    continue
                local_d_path = os.path.join(local_dir_path, d)
                if not os.path.exists(local_d_path):
                    self.dirs_to_create.append(os.path.join(rel_path, d))

            for f in files:

                if f in self.exclude_filenames:
                    continue

                if os.path.join(rel_path, f) in self.exclude_filepaths:
                    continue

                outputText = open(
                    os.path.join(dir_path, f), "r", encoding="latin-1"
                ).read()

                if ".tpl." in f:
                    template = Template(outputText)
                    outputText = template.render(
                        info=self.info, user_inputs=self.user_inputs
                    )

                rel_f_path = os.path.join(rel_path, f.replace(".tpl.", "."))
                self.files_to_add[rel_f_path] = outputText

    def custom_file_manipulation(self) -> None:
        pass

    def apply(self) -> None:

        """"""

        dirs_to_create = [
            os.path.join(self.local_path, tmp) for tmp in self.dirs_to_create
        ]

        files_to_create = {
            os.path.join(self.local_path, key): text
            for key, text in self.files_to_add.items()
            if not os.path.exists(os.path.join(self.local_path, key))
        }

        files_to_append = {
            os.path.join(self.local_path, key): text
            for key, text in self.files_to_add.items()
            if os.path.exists(os.path.join(self.local_path, key))
        }

        if not self.autoconfirm:

            click.secho("DIRECTORIES TO BE CREATED:", fg="green", bold=True)
            for key in dirs_to_create:
                click.secho(key, fg="green")

            click.secho("FILES TO BE CREATED:", fg="green", bold=True)
            for key, text in files_to_create.items():
                click.secho(key, fg="green")

            click.secho("FILES TO BE APPENDED:", fg="yellow", bold=True)
            for key, text in files_to_append.items():
                click.secho(key, fg="yellow")
                click.secho("\t+  ".join(("\n" + text).splitlines(True)) + "\n")

        if (not self.autoconfirm) and (
            not click.confirm("Do you want to continue?", default=True, abort=True)
        ):
            return

            # Print instructions
        if not self.autoconfirm:
            click.secho("INSTRUCTIONS", fg="green", bold=True)
            click.secho(self.instructions)
            click.secho("DEVELOPED BY:", fg="green", bold=True)
            click.secho(
                ", ".join(self.developers),
            )

        # Create and append files and dirs

        for directory in dirs_to_create:
            if not os.path.exists(directory):
                os.makedirs(directory)

        for key, text in files_to_create.items():
            directory = os.path.dirname(key)
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(key, "wb") as f:
                f.write(text.encode("latin-1"))

        for key, text in files_to_append.items():
            with open(key, "ab") as f:
                f.write(("\n\n" + text).encode("latin-1"))


def create_module_from_diff(module_name):

    if (
        subprocess.call(
            ["git", "branch"], stderr=subprocess.STDOUT, stdout=open(os.devnull, "w")
        )
        != 0
    ):
        click.Abort("Current directory is not a git repository")

    patch_file = f".rony_{module_name}.patch"
    module_path = os.path.join(os.path.expanduser("~"), "MyRonyModules", module_name)

    git_command = "git add -N -A; git diff --no-prefix"
    ret = subprocess.run(
        git_command,
        capture_output=True,
        shell=True,
    )

    patch_set = PatchSet(ret.stdout.decode())

    for patched_file in patch_set:

        file_path = patched_file.target_file
        added_lines = []
        for hunk in patched_file:
            for line in hunk:
                if line.is_added:
                    added_lines.append(line.value)

        module_file_path = os.path.join(module_path, file_path)
        module_dir_path = os.path.dirname(module_file_path)

        if not os.path.exists(module_dir_path):
            os.makedirs(module_dir_path)

        with open(module_file_path, "w") as f:
            f.write("".join(added_lines))

    info = click.prompt("Please your modules description", default="")
    inst = click.prompt(
        "Please instructions to be displayed to the users after they add this module",
        default="",
    )
    developer = click.prompt("Please enter your email", default="")

    with open(module_path + ".json", "w") as f:
        f.write(
            json.dumps(
                {
                    "info": info,
                    "instructions": [inst],
                    "developers": [developer],
                    "input_info": [],
                    "version": "0.0.0",
                    "dependencies": [],
                },
                sort_keys=True,
                indent=4,
                separators=(",", ": "),
            )
        )
