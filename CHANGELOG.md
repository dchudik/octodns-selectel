## v1.0.0 - 2024-02-01 - Added new SelectelProvider class to support DNS v2 API.

#### Changes

* Move existing provider and related tests to separate directories `v1`
* Rename public name from `SelectelProvider` to `SelectelProviderLegacy`
* Add `list_zones()` method to support "*" for planning
* Fix SSHFP parsing bug, caused by trailing dot in fingerprint which lead to constant re-update of record
* Move version varible to separate file, since now it is utilized by two providers. Storing it in `__init__.py` causes cycling imports
* Update `script/release` and `setup.py` to parse version from another location
* Update `readme.md` with focus on new provider

#### New

* Add new `SelectelProvider` class to support v2 API
* Isolate API calls into separate class
* Add tests for SelectelProvider

## v0.0.4 - 2023-12-06 - Bug fix

#### Changes

* Remove function forcing escaping semicolon in TXT content which caused record updating even if no changes were done to it 


## v0.0.3 - 2022-09-01 - New records and bug fix

#### Changes

* Add support for ALIAS and SSHFP record types
* Fix multiple records deletein bug


## v0.0.2 - 2022-04-19 - Minor update

#### Changes

* Removed SPF support, since Selectel API no longer supports it
* Fixed bug with wrong fqdn formatting during record deletion


## v0.0.1 - 2022-01-14 - Moving

#### Nothworthy Changes

* Initial extraction of SelectelProvider from octoDNS core

#### Stuff

Nothing
