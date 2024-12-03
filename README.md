Dataiku DSS collection
===================

This collection packages custom modules and roles to administrate Dataiku Data Science Studio platforms.


Installation
------------

### Basic

To install the collection in your default collections path:

 ```
ansible-galaxy collection install git+https://github.com/dataiku/dataiku-ansible-collection
 ```

To install in a custom path, you can set the `-p|--collections-path` flag.
Optionally, you can load collections from a custom path in ansible using the environment variable `ANSIBLE_COLLECTIONS_PATH` or by setting `collections_path` in `ansible.cfg`

```ini
# cat ansible.cfg
[defaults]
collections_path = <path to collections>  # note: path can be relative or absolute
```

### Force update

If the collection already exists, `ansible-galaxy` will not update it unless the `--force` flag is set.

### Automation and versioning

You can use a `yaml` file with a content like this:

```YAML
# cat requirements.yaml
---
collections:
  - source: https://github.com/dataiku/dataiku-ansible-collection
    name: dataiku.dss
    type: git
    version: main
```

Then install it like this:

```bash
ansible-galaxy install -r /path/to/your/requirements.yaml
```

This allows you to:
- Force a specific version
- Rename the role on the fly

Basic Usage
----------------

## Using Modules

```YAML
# cat ansible-playbook.yml
---
- hosts: servers
  become: true
  become_user: dataiku
  tasks:
    - dataiku.dss.dss_get_credentials:
        datadir: /home/dataiku/dss
        api_key_name: myadminkey
      register: dss_connection_info

    - dataiku.dss.dss_group:
        connect_to: "{{ dss_connection_info }}"
        name: datascienceguys

    - dataiku.dss.dss_user:
        connect_to: "{{ dss_connection_info }}"
        login: myadmin
        password: theadminpasswordveryverystrongindeed
        groups: [administrators,datascienceguys]

    - dataiku.dss.dss_general_settings:
        connect_to: "{{ dss_connection_info }}"
        settings:
          ldapSettings:
            enabled: true
            url: ldap://ldap.internal.example.com/dc=example,dc=com
            bindDN: uid=readonly,ou=users,dc=example,dc=com
            bindPassword: theserviceaccountpassword
            useTls: true
            autoImportUsers: true
            userFilter: (&(objectClass=posixAccount)(uid={USERNAME}))
            defaultUserProfile: READER
            displayNameAttribute: gecos
            emailAttribute: mail
            enableGroups: true
            groupFilter: (&(objectClass=posixGroup)(memberUid={USERDN}))
            groupNameAttribute: cn
            groupProfiles: []
            authorizedGroups: 
              - dss-users
```

## Using Roles

Using Roles from a playbook
```YAML
# cat ansible-playbook.yml
---
- hosts: servers
  become: true
  roles:
    - name: dataiku.dss.install_telegraf
      vars:
        telegraf_conf_dss_datadir: /data/dataiku/dss_data
        telegraf_conf_dss_id: test-collections
        telegraf_hostname: dss.example.com
    
    - name: dataiku.dss.install_tesseract
      vars:
        force_install: "{{ dataiku_dss_was_installed or dataiku_dss_was_upgraded }}"
```

Using Roles from a task
```YAML
# cat ansible-playbook.yml
---
tasks:
  - import_role:
      name: dataiku.dss.install_telegraf
    vars:
      telegraf_conf_dss_datadir: /data/dataiku/dss_data
      telegraf_conf_dss_id: test-collections
      telegraf_hostname: dss.example.com

  - import_role:
      name: dataiku.dss.install_tesseract
    vars:
      force_install: "{{ dataiku_dss_was_installed or dataiku_dss_was_upgraded }}"
```


Migrating from dataiku-ansible-modules
-----------------------------------------

The modules published in this collection are the same as the modules published in dataiku-ansible-modules. Their usage is the same, the only required changes are the way ansible access modules of collections.
In a collection, modules are referenced as `collection_namespace.collection_name.module_name`

Therefore, the module usage
```YAML
# cat ansible-playbook.yml
---
- hosts: servers
  become: true
  become_user: dataiku
  tasks:
    - dss_get_credentials:          # becomes dataiku.dss.dss_get_credentials
        datadir: /home/dataiku/dss
        api_key_name: myadminkey
      register: dss_connection_info
```

simply becomes :
```YAML
# cat ansible-playbook.yml
---
- hosts: servers
  become: true
  become_user: dataiku
  tasks:
    - dataiku.dss.dss_get_credentials:
        datadir: /home/dataiku/dss
        api_key_name: myadminkey
      register: dss_connection_info
```
