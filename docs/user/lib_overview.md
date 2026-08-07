# Library Overview

This document provides an overview of the library including critical information and important considerations.

## Description

Schema Enforcer requires that two different elements be defined by the user:

- Schema Definition Files: These are files which define the schema to which a given set of data should adhere.
- Structured Data Files: These are files which contain data that should adhere to the schema defined in one (or multiple) of the schema definition files.

> Note: Data which needs to be validated against a schema definition can come in the form of Structured Data Files or Ansible host vars. Ansible is not installed by default when schema-enforcer is installed. In order to use Ansible features, ansible must already be available or must be declared as an optional dependency when schema-enforcer upon installation. In the interest of brevity and simplicity, this README.md contains discussion only of Structured Data Files -- for more information on how to use `schema-enforcer` with ansible host vars, see [the ansible_command README](../user/ansible_command.md)

## Audience (User Personas) - Who should use this Library?

The intended audience is those who are programming with Python and specifically with JSON encoded data. Whether you are a seasoned veteran or a casual coder, this library should help to validate structured data or ansible host vars against a schema.

## Authors and Maintainers

- @cmsirbu
- @glennmatthews
- @PhillSimonds
- @dgarros
