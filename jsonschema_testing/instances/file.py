import os
import re
import itertools
from pathlib import Path
from jsonschema_testing.utils import find_files, load_file

SCHEMA_TAG = "jsonschema"


class InstanceFileManager:
    def __init__(self, search_directories, excluded_filenames, schema_mapping):

        self.instances = []

        files = find_files(
            file_extensions=[".yaml", ".yml", ".json"],
            search_directories=search_directories,
            excluded_filenames=excluded_filenames,
            return_dir=True,
        )

        for root, filename in files:

            matches = []
            if filename in schema_mapping:
                matches.extend(schema_mapping[filename])

            instance = InstanceFile(root=root, filename=filename, matches=matches)
            self.instances.append(instance)

    def print_instances_schema_mapping(self):

        print("Instance File                                     Schema")
        print("-" * 80)

        for instance in self.instances:
            filepath = f"{instance.path}/{instance.filename}"
            print(f"{filepath:50} {instance.matches}")
        # for instance_file, schema in instance_file_to_schemas_mapping.items():
        #     print(f"{instance_file:50} {schema}")
        # sys.exit(0)


class InstanceFile:
    def __init__(self, root, filename, matches=None):

        self.data = None
        self.path = root
        self.full_path = os.path.realpath(root)
        self.filename = filename

        if matches:
            self.matches = matches
        else:
            self.matches = []

        self.find_matches_inline()

    def find_matches_inline(self):

        contents = Path(os.path.join(self.full_path, self.filename)).read_text()
        matches = []

        if SCHEMA_TAG in contents:
            line_regexp = r"^#.*{0}:\s*(.*)$".format(SCHEMA_TAG)
            m = re.match(line_regexp, contents, re.MULTILINE)
            if m:
                matches = [x.strip() for x in m.group(1).split(",")]

        self.matches.extend(matches)

    def get_content(self):
        return load_file(os.path.join(self.full_path, self.filename))

    def validate(self, schema_manager, strict=False):

        # TODO check if a schema is missing

        errs = itertools.chain()

        # for gen in gens:
        # output = itertools.chain(output, gen)

        for schema_id, schema in schema_manager.iter_schemas():

            if schema_id not in self.matches:
                continue

            errs = itertools.chain(errs, schema.validate(self.get_content(), strict))

        return errs
