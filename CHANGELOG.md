# Changelog

# [v1.4.0] - 2025-07-21

### Added

- Publish collection to galaxy
- Added CI/CD for the collection
- Support cgroup v2 in telegraf probes

### Changed
### Fixed

- Removed docker input deprecated arguments from telegraf default configuration

# [v1.3.2] - 2025-05-02

### Added

- Added support to filter instances based on a tag on `fm_dss` inventory plugin

### Changed
### Fixed

- Fixed installation of a specific version of telegraf
- Fixed file permission issue while installing telegraf on rpm distros
- Removed duplicate entries from telegraf configuration

# [v1.3.1] - 2025-01-30
### Added

- Added support for collecting DSS metrics from he prometheus endpoint

### Changed
### Fixed

- Added missing group permissions in `dss_group` ansible module
- Fix incorrect file permissions while install tesseract 
- Handle edge case when there are no existing keys in `dss_get_credentials`

# [v1.3.0] - 2024-10-25

### Added
 
- Added support for hashed api keys in `dss_get_credentials` ansible module
- Support all group types in `dss_group` ansible module

### Changed

- Do not return stopped instances in `fm_dss` ansible inventory
- Only return memory limit and usage from telegraf [cgroup](https://github.com/influxdata/telegraf/blob/master/plugins/inputs/cgroup/README.md) probe
- Adapt telegraf probes to govern node

### Fixed

- Improved documentation

# [v1.2.1] - 2024-07-01

### Added

- Added `fm_dss` inventory plugin

### Changed

- Added [linux_sysctl_fs](https://github.com/influxdata/telegraf/blob/master/plugins/inputs/linux_sysctl_fs/README.md) telegraf input in DSS default probes

### Fixed

- Handled edge cases with LDAP groups after DSS 12.6 upgrade
- Fixed global tags of metrics exposed by telegraf
- Fixed dss plugin installation from archive
- Do not install stories probes if stories is not installed


# [v1.2.0] - 2024-05-15

### Added

- Added support of smart update of named fields in settings

### Changed
### Fixed

# [v1.0.1] - 2024-05-07

### Added

- Added `install_tesseract` ansible role

### Changed

- Improved documentation on monitoring installation

### Fixed

- Handled some edge cases on `get_client_from_parsed_args`

# [v1.0.0] - 2024-05-06

Migrated all modules from https://github.com/dataiku/dataiku-ansible-modules

### Added

- Added `dss_api_deployer_infra` ansible module
- Added `dss_code_env` ansible module
- Added `dss_connection_generic` ansible module
- Added `dss_connection_postgresql` ansible module
- Added `dss_general_settings` ansible module
- Added `dss_get_credentials` ansible module
- Added `dss_group` ansible module
- Added `dss_plugin` ansible module
- Added `dss_system_facts` ansible module
- Added `dss_user` ansible module
- Added `install_telegraf` ansible role

### Changed

- `dataiku.dssclient` is now directly imported from dss

### Fixed
