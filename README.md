# Schema Enforcer

<p align="center">
  <img src="https://raw.githubusercontent.com/networktocode/schema-enforcer/develop/docs/images/icon-schema-enforcer.png" class="logo" height="200px">
  <br>
  <a href="https://github.com/networktocode/schema-enforcer/actions"><img src="https://github.com/networktocode/schema-enforcer/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="https://schema-enforcer.readthedocs.io/en/latest/"><img src="https://readthedocs.org/projects/schema-enforcer/badge/"></a>
  <a href="https://pypi.org/project/schema-enforcer/"><img src="https://img.shields.io/pypi/v/schema-enforcer"></a>
  <a href="https://pypi.org/project/schema-enforcer/"><img src="https://img.shields.io/pypi/dm/schema-enforcer"></a>
  <br>
</p>

## Overview

Schema Enforcer provides a framework for testing structured data against schema definitions using [JSONSchema](https://json-schema.org/understanding-json-schema/index.html).

## Documentation

Full documentation for this library can be found over on the [Schema Enforcer Docs](https://schema-enforcer.readthedocs.io/) website:

- [User Guide](https://schema-enforcer.readthedocs.io/en/latest/user/app_overview/) - Overview, Using the Library, Getting Started.
- [Administrator Guide](https://schema-enforcer.readthedocs.io/en/latest/admin/install/) - How to Install, Configure, Upgrade, or Uninstall the Library.
- [Developer Guide](https://schema-enforcer.readthedocs.io/en/latest/dev/contributing/) - Extending the Library, Code Reference, Contribution Guide.
- [Release Notes / Changelog](https://schema-enforcer.readthedocs.io/en/latest/admin/release_notes/).
- [Frequently Asked Questions](https://schema-enforcer.readthedocs.io/en/latest/user/faq/).

### Contributing to the Documentation

You can find all the Markdown source for the App documentation under the [`docs`](https://github.com/networktocode/schema-enforcer/tree/develop/docs) folder in this repository. For simple edits, a Markdown capable editor is sufficient: clone the repository and edit away.

If you need to view the fully-generated documentation site, you can build it with [MkDocs](https://www.mkdocs.org/). A container hosting the documentation can be started using the `invoke` commands (details in the [Development Environment Guide](https://schema-enforcer/dev/dev_environment/#docker-development-environment)) on [http://localhost:8001](http://localhost:8001). Using this container, as your changes to the documentation are saved, they will be automatically rebuilt and any pages currently being viewed will be reloaded in your browser.

Any PRs with fixes or improvements are very welcome!

## Questions

For any questions or comments, please check the [FAQ](https://schema-enforcer.readthedocs.io/en/latest/user/faq/) first. Feel free to also swing by the [Network to Code Slack](https://networktocode.slack.com/) (channel `#networktocode`), sign up [here](http://slack.networktocode.com/) if you don't have an account.
