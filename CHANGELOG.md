# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3]

Fixed bug which was making TinyEntity hang when you tried to iterate over
its properties with [ for blah in entity ]

Made TinyEntity properties all return values as lists

## [0.1.2]

Fixed auto date bug, added type annotations to tinycrate.py

## [0.1.1]

Fixed Windows encoding bugs, added context resolver and CI, made it able to
load a completey networked crate

## [0.1.0]

Initial version broken out from rocrate-tabular
