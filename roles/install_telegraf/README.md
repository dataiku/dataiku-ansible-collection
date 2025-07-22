# Install telegraf

This role installs telegraf with the default configuration to monitor DSS

## Usage

```yaml
- name: Install telegraf and configure probes
  ansible.builtin.import_role:
    name: dataiku.dss.install_telegraf
  vars:
    telegraf_conf_dss_datadir: /data/dataiku/dss_data
    telegraf_conf_dss_installdir: /opt/dataiku-dss-14.0.0
    telegraf_conf_dss_node_type: design
    telegraf_conf_dss_story_enabled: true
    telegraf_hostname: my-design.example.com
    telegraf_conf_dss_id: my-design
```

Additionally, to collect information directly from DSS:

```yaml
- name: Parse env-default.sh file
  block:
    - name: Fetch env-default.sh content
      ansible.builtin.slurp:
        src: /data/dataiku/dss_data/bin/env-default.sh
      register: env_default

    - ansible.builtin.set_fact:
        dss_installdir: "{{ env_default['content'] | b64decode | regex_search('export DKUINSTALLDIR=\"(.+)\"', '\\1') | first }}"

- name: Fetch DSS system facts
  become: true
  become_user: dataiku
  dataiku.dss.dss_system_facts:
    datadir: /data/dataiku/dss_data
  register: dss_system_facts

- name: Install telegraf and configure probes
  ansible.builtin.import_role:
    name: dataiku.dss.install_telegraf
  vars:
    telegraf_conf_dss_datadir: /data/dataiku/dss_data
    telegraf_conf_dss_installdir: "{{ dss_installdir }}"
    telegraf_conf_dss_node_type: "{{ dss_system_facts.install_ini.general.nodetype }}"
    telegraf_conf_dss_story_enabled: "{{ dss_system_facts.install_ini.story.enabled | default(false) }}"
    telegraf_hostname: "my-design.example.com"
    telegraf_conf_dss_id: "production-{{ dss_system_facts.install_ini.general.nodeid }}"
    telegraf_global_tags:
      dss_id: "{{ telegraf_conf_dss_id }}"
      environment: "production"
```
 
## Expected behavior

This role installs telegraf and a default configuration to monitor DSS. 
Telegraf is installed as a systemd service and loads its configuration from `/etc/telegraf/telegraf.d/` with:
- `/etc/telegraf/telegraf.conf` -> the core telegraf configuration
- `/etc/telegraf/telegraf.d/dss-inputs.conf` -> the telegraf configuration for inputs
- `/etc/telegraf/telegraf.d/dss-outputs.conf` -> the telegraf configuration for outputs
- `/etc/telegraf/telegraf.d/dss-additional.conf` -> the telegraf configuration for any additional configuration

All these configurations can be overridden by providing `telegraf_conf_core_content`, `telegraf_conf_inputs_content`, `telegraf_conf_outputs_content` and `telegraf_conf_additional_content`

## Providing secrets

Telegraf can be customized to load secrets stored onto the filesystem. By default, it will read the secrets from `/etc/telegraf/telegraf.secrets`

```yaml
- name: Create telegraf secrets file
  ansible.builtin.copy:
  content: "DSS_API_KEY={{ dss_credentials['api_key'] }}"
  dest: /etc/telegraf/telegraf.secrets
  mode: "400"
  owner: telegraf
  group: telegraf
```

Telegraf can also load secrets from multiple locations:

```yaml
- name: Add systemd environment file
  become: true
  ansible.builtin.lineinfile:
    path: /etc/systemd/system/telegraf.service.d/override.conf
    line: EnvironmentFile=-/data/etc/telegraf/telegraf.secrets

- name: Daemon reload
  ansible.builtin.systemd:
    daemon_reload: true
    name: telegraf
    state: restarted
    enabled: true  
```

## Available inputs

This role accepts the following inputs

| Input                             | Required | Type   | Default                                                                                                                                                                                 | Comment                                                                |
|-----------------------------------|----------|--------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| telegraf_version                  | true     | str    | null                                                                                                                                                                                    | The telegraf version to install. If empty, installs the latest version |
| telegraf_conf_dss_datadir         | true     | str    | null                                                                                                                                                                                    | DSS's data_dir                                                         |                                                                    
| telegraf_conf_dss_installdir      | true     | str    | null                                                                                                                                                                                    | DSS's install_dir                                                      |
| telegraf_conf_dss_id              | true     | str    | null                                                                                                                                                                                    | The ID of the DSS (used in for tagging metrics)                        |
| telegraf_conf_dss_node_type       | true     | str    | null                                                                                                                                                                                    | DSS's node type                                                        |
| telegraf_conf_dss_story_enabled   | false    | bool   | false                                                                                                                                                                                   | Whether stories is enabled on DSS                                      |
| telegraf_conf_use_legacy_graphite | false    | bool   | false                                                                                                                                                                                   | Whether to collect metrics from DSS using the Graphite endpoint        |
| telegraf_global_tags              | false    | object | {"dss_id": "{{ telegraf_conf_dss_id }}" }                                                                                                                                               | Mapping of tags applied to metrics                                     |
| telegraf_hostname                 | false    | str    | null                                                                                                                                                                                    | The hostname of the instance                                           |
| telegraf_conf_core_content        | false    | str    | [see code](defaults/main.yml)                                                                                                                                                           | The telegraf core configuration                                        |
| telegraf_conf_inputs_content      | false    | str    | [see code](defaults/main.yml)                                                                                                                                                           | The telegraf inputs configuration                                      |
| telegraf_conf_outputs_content     | false    | str    | [see code](defaults/main.yml)                                                                                                                                                           | The telegraf outputs configuration                                     |
| telegraf_conf_additional_content  | false    | str    | ""                                                                                                                                                                                      | The telegraf additional configuration                                  |
| telegraf_cgroupv1_enabled         | false    | bool   | true                                                                                                                                                                                    | Whether to collect cgroupv1 metrics                                    |
| telegraf_cgroupv2_enabled         | false    | bool   | true                                                                                                                                                                                    | Whether to collect cgroupv2 metrics                                    |
| telegraf_cgroupv1_paths           | false    | list   | ["/sys/fs/cgroup/memory/DSS", "/sys/fs/cgroup/memory/DSS/\*", "/sys/fs/cgroup/memory/DSS/\*/\*", "/sys/fs/cgroup/cpu/DSS", "/sys/fs/cgroup/cpu/DSS/\*", "/sys/fs/cgroup/cpu/DSS/\*/\*"] | The list of cgroupv1 paths to look for                                 |
| telegraf_cgroupv1_files           | false    | list   | ["memory.\*usage\*", "memory.limit_in_bytes", "cpuacct.\*usage\*", "cpu.shares"]                                                                                                        | The list of cgroupv1 files to look for                                 |
| telegraf_cgroupv2_paths           | false    | list   | ["/sys/fs/cgroup/DSS", "/sys/fs/cgroup/DSS/\*", "/sys/fs/cgroup/DSS/\*/\*"]                                                                                                             | The list of cgroupv2 paths to look for                                 |
| telegraf_cgroupv2_files           | false    | list   | ["memory.max", "memory.current", "cpu.weight", "cpu.max", "cpu.stat"]                                                                                                                   | The list of cgroupv2 files to look for                                 |
